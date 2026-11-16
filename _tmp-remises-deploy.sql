-- Tikette : remises et cadeaux réservés aux abonnés Tikette Or chez les partenaires (décision de Greg, 14 nov. 2026).
--
-- Le partenaire décide de tout, depuis son espace pro :
--   • une remise (-5 % à -50 %) ou un cadeau (« un cocktail offert », « 15 min de plus »…) ;
--   • sur une activité ou sur toutes ;
--   • pour quand : du … au … (un jour, une semaine, un mois…, un an au plus), et s'il veut seulement certains jours
--     de la semaine (ex. mardi et mercredi).
-- C'est la date de la sortie qui compte (pas celle de la réservation) : le pro remplit ses jours creux.
-- Tikette ne paie jamais la remise : c'est le partenaire qui la fait. Notre commission est calculée sur le prix remisé.
-- Seuls les abonnés Tikette Or en profitent ; les autres la voient (grisée) dans l'appli.
--
-- À lancer dans Supabase › SQL Editor APRÈS pro.sql, pro-messages.sql et photos-pro.sql.
-- Relançable sans risque. À RELANCER après chaque nouveau lancement de pro.sql, pro-messages.sql ou photos-pro.sql
-- (ce fichier remplace pro_reserver, pro_offres_autour, pro_offre, pro_reservations_liste et pro_mails_a_envoyer).

-- ───────────────────────── Les remises ─────────────────────────
create table if not exists public.pro_remises_or (
  id uuid primary key default gen_random_uuid(),
  entreprise_id uuid not null references public.pro_entreprises (id) on delete cascade,
  offre_id uuid references public.pro_offres (id) on delete cascade,      -- null = toutes les activités
  genre text not null check (genre in ('remise', 'cadeau')),
  pourcentage int not null default 0,
  cadeau text not null default '' check (length(cadeau) <= 80),
  du date not null,
  au date not null,
  jours smallint[] not null default '{}',                                  -- 1 = lundi … 7 = dimanche ; vide = tous les jours
  actif boolean not null default true,
  cree_le timestamptz not null default now(),
  check (au >= du and au - du <= 366),
  check ((genre = 'remise' and pourcentage between 5 and 50) or (genre = 'cadeau' and pourcentage = 0 and length(trim(cadeau)) >= 3)),
  check (jours <@ array[1,2,3,4,5,6,7]::smallint[])
);
create index if not exists pro_remises_or_ent on public.pro_remises_or (entreprise_id, au);
alter table public.pro_remises_or enable row level security;
revoke all on public.pro_remises_or from anon, authenticated;

-- Ce que l'abonné a eu sur sa réservation (montré au pro et au client).
alter table public.pro_reservations add column if not exists remise_pct int not null default 0;
alter table public.pro_reservations add column if not exists cadeau_or text not null default '';
alter table public.pro_reservations add column if not exists prix_normal_cents int;

-- La meilleure remise Or d'une activité pour une sortie à cette heure-là (la plus forte remise, sinon un cadeau).
create or replace function public.pro_remise_du(p_offre uuid, p_debut timestamptz)
returns table (pourcentage int, cadeau text)
language sql stable security definer set search_path = '' as $$
  select r.pourcentage, r.cadeau
    from public.pro_remises_or r join public.pro_offres o on o.entreprise_id = r.entreprise_id
   where o.id = p_offre and r.actif and (r.offre_id is null or r.offre_id = p_offre)
     and (p_debut at time zone 'Europe/Paris')::date between r.du and r.au
     and (cardinality(r.jours) = 0 or extract(isodow from p_debut at time zone 'Europe/Paris')::smallint = any (r.jours))
   order by (r.genre = 'remise') desc, r.pourcentage desc, r.cree_le
   limit 1;
$$;

-- Les remises à venir d'une activité (pour l'appli : badge « -20 % avec Tikette Or » sur les bons jours).
create or replace function public.pro_remises_publiques(p_offre uuid, p_entreprise uuid)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('genre', r.genre, 'pourcentage', r.pourcentage, 'cadeau', r.cadeau,
           'du', r.du, 'au', r.au, 'jours', to_jsonb(r.jours)) order by r.du), '[]'::jsonb)
    from public.pro_remises_or r
   where r.entreprise_id = p_entreprise and r.actif and (r.offre_id is null or r.offre_id = p_offre)
     and r.au >= (now() at time zone 'Europe/Paris')::date;
$$;

-- L'utilisateur connecté a-t-il Tikette Or en ce moment ?
create or replace function public.pro_client_or(p_user uuid)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.premium where user_id = p_user and jusquau > now());
$$;

-- ───────────────────────── Espace pro ─────────────────────────

-- Mes remises (en cours et à venir d'abord, puis les 20 dernières passées).
create or replace function public.pro_remises()
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', r.id, 'offre_id', r.offre_id, 'offre', o.titre, 'genre', r.genre,
           'pourcentage', r.pourcentage, 'cadeau', r.cadeau, 'du', r.du, 'au', r.au, 'jours', to_jsonb(r.jours), 'actif', r.actif,
           'reservations', s.n, 'offert_cents', s.offert)
         order by (r.au >= (now() at time zone 'Europe/Paris')::date) desc, r.du), '[]'::jsonb)
    from (select * from public.pro_remises_or where entreprise_id = public.pro_mon_entreprise()
           order by (au >= (now() at time zone 'Europe/Paris')::date) desc, au desc limit 60) r
    left join public.pro_offres o on o.id = r.offre_id
    cross join lateral (select count(*) n, coalesce(sum(greatest(coalesce(pr.prix_normal_cents, pr.prix_cents) - pr.prix_cents, 0)), 0) offert
                          from public.pro_reservations pr where pr.entreprise_id = r.entreprise_id
                           and (pr.remise_pct > 0 or pr.cadeau_or <> '') and pr.statut in ('demandee', 'confirmee', 'venue')
                           and (r.offre_id is null or pr.offre_id = r.offre_id)
                           and (pr.debut at time zone 'Europe/Paris')::date between r.du and r.au
                           and (r.genre = 'remise') = (pr.remise_pct > 0)) s;
$$;

-- Créer ou modifier une remise. p = { id?, offre_id? (null = toutes), genre, pourcentage | cadeau, du, au, jours?, actif? }
create or replace function public.pro_enregistrer_remise(p jsonb)
returns uuid language plpgsql security definer set search_path = '' as $$
declare
  v_ent uuid := public.pro_mon_entreprise(); v_id uuid := nullif(p->>'id', '')::uuid; v_offre uuid := nullif(p->>'offre_id', '')::uuid;
  v_genre text := p->>'genre'; v_pct int := coalesce((p->>'pourcentage')::int, 0); v_cadeau text := left(trim(coalesce(p->>'cadeau', '')), 80);
  v_du date := (p->>'du')::date; v_au date := (p->>'au')::date; v_jours smallint[];
  v_auj date := (now() at time zone 'Europe/Paris')::date;
begin
  if v_ent is null then raise exception 'Espace pro introuvable.'; end if;
  if v_genre not in ('remise', 'cadeau') then raise exception 'Choisissez une remise ou un cadeau.'; end if;
  if v_genre = 'remise' then
    if v_pct < 5 or v_pct > 50 then raise exception 'La remise va de 5 %% à 50 %%.'; end if;
    v_cadeau := '';
  else
    if length(v_cadeau) < 3 then raise exception 'Décrivez le cadeau (ex. « Un cocktail offert »).'; end if;
    v_pct := 0;
  end if;
  if v_du is null or v_au is null then raise exception 'Choisissez les dates.'; end if;
  if v_au < v_du then raise exception 'La date de fin est avant la date de début.'; end if;
  if v_au < v_auj then raise exception 'Ces dates sont déjà passées.'; end if;
  if v_au - v_du > 366 then raise exception 'Une remise dure un an au plus.'; end if;
  if v_du > v_auj + 365 then raise exception 'Une remise commence dans l''année qui vient.'; end if;
  if v_offre is not null and not exists (select 1 from public.pro_offres where id = v_offre and entreprise_id = v_ent) then
    raise exception 'Activité introuvable.';
  end if;
  select coalesce(array_agg(distinct j order by j), '{}') into v_jours
    from (select (x)::smallint j from jsonb_array_elements_text(coalesce(p->'jours', '[]')) x where x ~ '^[1-7]$') t;
  if cardinality(v_jours) = 7 then v_jours := '{}'; end if;
  if v_id is null then
    if (select count(*) from public.pro_remises_or where entreprise_id = v_ent and au >= v_auj) >= 20 then
      raise exception '20 remises en cours ou à venir au plus.';
    end if;
    insert into public.pro_remises_or (entreprise_id, offre_id, genre, pourcentage, cadeau, du, au, jours, actif)
    values (v_ent, v_offre, v_genre, v_pct, v_cadeau, v_du, v_au, v_jours, coalesce((p->>'actif')::boolean, true))
    returning id into v_id;
  else
    update public.pro_remises_or set offre_id = v_offre, genre = v_genre, pourcentage = v_pct, cadeau = v_cadeau,
      du = v_du, au = v_au, jours = v_jours, actif = coalesce((p->>'actif')::boolean, actif)
     where id = v_id and entreprise_id = v_ent;
    if not found then raise exception 'Remise introuvable.'; end if;
  end if;
  return v_id;
end $$;

-- Mettre en pause / reprendre, ou supprimer. Les réservations déjà faites gardent leur remise.
create or replace function public.pro_pause_remise(p_id uuid, p_actif boolean)
returns void language plpgsql security definer set search_path = '' as $$
begin
  update public.pro_remises_or set actif = p_actif where id = p_id and entreprise_id = public.pro_mon_entreprise();
  if not found then raise exception 'Remise introuvable.'; end if;
end $$;
create or replace function public.pro_supprimer_remise(p_id uuid)
returns void language plpgsql security definer set search_path = '' as $$
begin
  delete from public.pro_remises_or where id = p_id and entreprise_id = public.pro_mon_entreprise();
  if not found then raise exception 'Remise introuvable.'; end if;
end $$;

-- ───────────────────────── Appli : activités autour, une activité ─────────────────────────

create or replace function public.pro_offres_autour(p_lat double precision, p_lon double precision, p_rayon_km double precision)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(x order by x->>'distance'), '[]'::jsonb) from (
    select jsonb_build_object(
      'id', o.id, 'titre', o.titre, 'description', o.description, 'genre', o.genre, 'genres', o.genres, 'familles', (select coalesce(jsonb_agg(distinct t.famille), '[]') from public.pro_types t where t.id = any (o.genres)), 'ambiances', o.ambiances,
      'mode', o.mode, 'duree_min', o.duree_min, 'prix_cents', o.prix_cents, 'prix_par', o.prix_par,
      'min_personnes', o.min_personnes, 'max_personnes', o.max_personnes, 'confirmation', o.confirmation,
      'annulation_h', o.annulation_h, 'demander_prenoms', o.demander_prenoms, 'consignes', o.consignes, 'photos', case when cardinality(o.photos) > 0 then o.photos else e.photos end,
      'entreprise', e.nom, 'fondateur', e.fondateur, 'paiement', (e.stripe_paiements and e.stripe_compte is not null), 'lat', coalesce(o.lat, e.lat), 'lon', coalesce(o.lon, e.lon), 'adresse', case when o.adresse <> '' then o.adresse else e.adresse end, 'commune', case when o.commune <> '' then o.commune else e.commune end,
      'horaires', (select coalesce(jsonb_agg(jsonb_build_object('jour', h.jour, 'debut', to_char(h.debut, 'HH24:MI'), 'fin', to_char(h.fin, 'HH24:MI'))), '[]') from public.pro_horaires h where h.offre_id = o.id),
      'remises_or', public.pro_remises_publiques(o.id, e.id),
      'distance', round((6371 * acos(least(1, cos(radians(p_lat)) * cos(radians(coalesce(o.lat, e.lat))) * cos(radians(coalesce(o.lon, e.lon)) - radians(p_lon)) + sin(radians(p_lat)) * sin(radians(coalesce(o.lat, e.lat))))))::numeric, 1)
    ) as x
      from public.pro_offres o join public.pro_entreprises e on e.id = o.entreprise_id
     where o.actif and e.statut = 'valide' and coalesce(o.lat, e.lat) is not null
       and exists (select 1 from public.pro_horaires h where h.offre_id = o.id)
       and exists (select 1 from public.pro_ressources r where r.offre_id = o.id and r.actif)
       and 6371 * acos(least(1, cos(radians(p_lat)) * cos(radians(coalesce(o.lat, e.lat))) * cos(radians(coalesce(o.lon, e.lon)) - radians(p_lon)) + sin(radians(p_lat)) * sin(radians(coalesce(o.lat, e.lat))))) <= least(p_rayon_km, 80)
     limit 200
  ) t;
$$;

create or replace function public.pro_offre(p_id uuid)
returns jsonb language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
      'id', o.id, 'titre', o.titre, 'description', o.description, 'genre', o.genre, 'genres', o.genres,
      'familles', (select coalesce(jsonb_agg(distinct t.famille), '[]') from public.pro_types t where t.id = any (o.genres)), 'ambiances', o.ambiances,
      'mode', o.mode, 'duree_min', o.duree_min, 'prix_cents', o.prix_cents, 'prix_par', o.prix_par,
      'min_personnes', o.min_personnes, 'max_personnes', o.max_personnes, 'confirmation', o.confirmation,
      'annulation_h', o.annulation_h, 'consignes', o.consignes, 'photos', case when cardinality(o.photos) > 0 then o.photos else e.photos end,
      'entreprise', e.nom, 'fondateur', e.fondateur, 'paiement', (e.stripe_paiements and e.stripe_compte is not null),
      'lat', coalesce(o.lat, e.lat), 'lon', coalesce(o.lon, e.lon), 'adresse', case when o.adresse <> '' then o.adresse else e.adresse end, 'commune', case when o.commune <> '' then o.commune else e.commune end,
      'horaires', (select coalesce(jsonb_agg(jsonb_build_object('jour', h.jour, 'debut', to_char(h.debut, 'HH24:MI'), 'fin', to_char(h.fin, 'HH24:MI'))), '[]') from public.pro_horaires h where h.offre_id = o.id),
      'remises_or', public.pro_remises_publiques(o.id, e.id))
    from public.pro_offres o join public.pro_entreprises e on e.id = o.entreprise_id
   where o.id = p_id and o.actif and e.statut = 'valide' and coalesce(o.lat, e.lat) is not null;
$$;

-- ───────────────────────── Réserver (avec la remise Or) ─────────────────────────
create or replace function public.pro_reserver(p_offre uuid, p_debut timestamptz, p_personnes int,
  p_ressource uuid default null, p_prenom text default '', p_message text default '',
  p_groupe text default '', p_participants text[] default '{}')
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_uid uuid := auth.uid(); o record; e record; r record; v_res uuid; v_code text; v_id uuid; v_statut text;
  v_libres int; v_prix int; v_normal int; v_pct int := 0; v_cadeau text := ''; v_or boolean; rem record;
begin
  if v_uid is null then return jsonb_build_object('ok', false, 'raison', 'connexion'); end if;
  select * into o from public.pro_offres where id = p_offre and actif;
  select * into e from public.pro_entreprises where id = o.entreprise_id and statut = 'valide';
  if o.id is null or e.id is null then return jsonb_build_object('ok', false, 'raison', 'indisponible'); end if;
  if p_personnes is null or p_personnes < o.min_personnes or p_personnes > o.max_personnes then
    return jsonb_build_object('ok', false, 'raison', 'personnes', 'min', o.min_personnes, 'max', o.max_personnes);
  end if;
  if (select count(*) from public.pro_reservations where user_id = v_uid and cree_le > now() - interval '1 day') >= 10 then
    return jsonb_build_object('ok', false, 'raison', 'limite');
  end if;
  -- Un verrou par activité et par heure : les réservations simultanées passent l'une après l'autre.
  perform pg_advisory_xact_lock(hashtext(p_offre::text || p_debut::text));
  for r in select d.ressource_id, d.places from public.pro_disponibilites(p_offre,
             (p_debut at time zone 'Europe/Paris')::date, (p_debut at time zone 'Europe/Paris')::date) d
           where d.debut = p_debut and (p_ressource is null or d.ressource_id = p_ressource)
           order by d.places loop
    if r.places >= p_personnes then v_res := r.ressource_id; exit; end if;
  end loop;
  if v_res is null then return jsonb_build_object('ok', false, 'raison', 'pris'); end if;
  v_normal := case when o.prix_par = 'personne' then o.prix_cents * p_personnes else o.prix_cents end;
  v_prix := v_normal;
  -- Remise ou cadeau Tikette Or : seulement pour les abonnés, décidé et payé par le partenaire.
  v_or := public.pro_client_or(v_uid);
  if v_or then
    select * into rem from public.pro_remise_du(o.id, p_debut);
    if rem.pourcentage is not null then
      v_pct := rem.pourcentage; v_cadeau := coalesce(rem.cadeau, '');
      if v_pct > 0 then v_prix := round(v_normal * (100 - v_pct) / 100.0)::int; end if;
    end if;
  end if;
  v_statut := case when o.confirmation = 'immediate' then 'confirmee' else 'demandee' end;
  -- Partenaire relié à Stripe et activité payante : on paie d'abord (créneau gardé 15 min), la demande part au pro ensuite.
  if e.stripe_paiements and e.stripe_compte is not null and v_prix >= 50 then v_statut := 'a_payer'; end if;
  loop
    v_code := public.pro_code();
    exit when not exists (select 1 from public.pro_reservations where code = v_code);
  end loop;
  insert into public.pro_reservations (code, offre_id, ressource_id, entreprise_id, user_id, prenom, message, groupe, participants,
      debut, fin, personnes, prix_cents, statut, repondre_avant, taux, paiement, payer_avant, remise_pct, cadeau_or, prix_normal_cents)
  values (v_code, o.id, v_res, e.id, v_uid, left(coalesce(p_prenom, ''), 40), left(coalesce(p_message, ''), 300),
      left(trim(coalesce(p_groupe, '')), 40),
      coalesce((select array_agg(left(trim(x), 30)) from (select x from unnest(p_participants) x where trim(x) <> '' limit 60) t), '{}'),
      p_debut,
      p_debut + make_interval(mins => o.duree_min), p_personnes, v_prix, v_statut,
      case when v_statut = 'demandee' then least(now() + make_interval(hours => o.delai_reponse_h), p_debut - interval '1 hour') end,
      public.pro_taux(e.fondateur, p_debut),
      case when v_statut = 'a_payer' then 'en_attente' else 'sur_place' end,
      case when v_statut = 'a_payer' then now() + interval '15 minutes' end,
      v_pct, v_cadeau, v_normal)
  returning id into v_id;
  if v_statut <> 'a_payer' then perform public.pro_notifier(v_id); end if;
  return jsonb_build_object('ok', true, 'id', v_id, 'code', v_code, 'statut', v_statut, 'prix_cents', v_prix,
    'prix_normal_cents', v_normal, 'remise_pct', v_pct, 'cadeau_or', v_cadeau, 'payer', v_statut = 'a_payer');
end $$;

-- ───────────────────────── Le partenaire voit la remise ─────────────────────────
create or replace function public.pro_reservations_liste(p_du timestamptz, p_au timestamptz)
returns jsonb language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', pr.id, 'code', pr.code, 'statut', pr.statut, 'motif', pr.motif,
    'debut', pr.debut, 'fin', pr.fin, 'personnes', pr.personnes, 'prix_cents', pr.prix_cents, 'prenom', pr.prenom,
    'message', pr.message, 'groupe', pr.groupe, 'participants', to_jsonb(pr.participants), 'note_pro', pr.note_pro,
    'offre_id', pr.offre_id, 'offre', o.titre, 'ressource_id', pr.ressource_id, 'ressource', r.nom,
    'repondre_avant', pr.repondre_avant, 'cree_le', pr.cree_le, 'paiement', pr.paiement,
    'remise_pct', pr.remise_pct, 'cadeau_or', pr.cadeau_or, 'prix_normal_cents', pr.prix_normal_cents,
    'commission_cents', case when pr.statut in ('venue', 'confirmee') then round(pr.prix_cents * pr.taux) else 0 end
  ) order by pr.debut), '[]'::jsonb)
  from public.pro_reservations pr join public.pro_offres o on o.id = pr.offre_id join public.pro_ressources r on r.id = pr.ressource_id
  where pr.entreprise_id = public.pro_mon_entreprise() and pr.debut >= p_du and pr.debut < p_au
    and pr.statut not in ('a_payer', 'non_payee');  -- paiement pas terminé : rien à voir pour le pro
$$;

create or replace function public.pro_mails_a_envoyer()
returns jsonb language plpgsql security definer set search_path = '' as $$
declare v jsonb;
begin
  with a as (
    insert into public.pro_mails_envoyes (reservation_id)
      select pr.id from public.pro_reservations pr join public.pro_entreprises en on en.id = pr.entreprise_id
       where pr.cree_le > now() - interval '1 day' and en.notif_mail and pr.statut in ('demandee', 'confirmee')
         and not exists (select 1 from public.pro_mails_envoyes m where m.reservation_id = pr.id) limit 100
    returning reservation_id
  )
  select coalesce(jsonb_agg(jsonb_build_object('email', e.email, 'copies', e.emails_copie, 'groupe', pr.groupe,
      'participants', to_jsonb(pr.participants), 'entreprise', e.nom, 'offre', o.titre, 'code', pr.code,
      'statut', pr.statut, 'debut', pr.debut, 'personnes', pr.personnes, 'prenom', pr.prenom, 'repondre_avant', pr.repondre_avant,
      'remise_pct', pr.remise_pct, 'cadeau_or', pr.cadeau_or)), '[]')
    into v
    from a join public.pro_reservations pr on pr.id = a.reservation_id join public.pro_offres o on o.id = pr.offre_id
    join public.pro_entreprises e on e.id = pr.entreprise_id;
  return v;
end $$;

-- ───────────────────────── Droits ─────────────────────────
do $$
declare f text;
begin
  foreach f in array array['pro_remise_du(uuid,timestamptz)', 'pro_remises_publiques(uuid,uuid)', 'pro_client_or(uuid)',
    'pro_remises()', 'pro_enregistrer_remise(jsonb)', 'pro_pause_remise(uuid,boolean)', 'pro_supprimer_remise(uuid)',
    'pro_offres_autour(double precision,double precision,double precision)', 'pro_offre(uuid)',
    'pro_reserver(uuid,timestamptz,int,uuid,text,text,text,text[])', 'pro_reservations_liste(timestamptz,timestamptz)',
    'pro_mails_a_envoyer()'] loop
    execute 'revoke all on function public.' || f || ' from public, anon, authenticated';
  end loop;
  foreach f in array array['pro_offres_autour(double precision,double precision,double precision)', 'pro_offre(uuid)'] loop
    execute 'grant execute on function public.' || f || ' to anon, authenticated';
  end loop;
  foreach f in array array['pro_remises()', 'pro_enregistrer_remise(jsonb)', 'pro_pause_remise(uuid,boolean)', 'pro_supprimer_remise(uuid)',
    'pro_reserver(uuid,timestamptz,int,uuid,text,text,text,text[])', 'pro_reservations_liste(timestamptz,timestamptz)'] loop
    execute 'grant execute on function public.' || f || ' to authenticated';
  end loop;
  execute 'grant execute on function public.pro_mails_a_envoyer() to service_role';
end $$;
