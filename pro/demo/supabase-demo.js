// Démonstration : remplace Supabase par des données d'exemple gardées dans la page (rien n'est envoyé ni enregistré).
(function () {
  const TZ = 'Europe/Paris';
  const auj = new Date().toLocaleDateString('fr-CA', { timeZone: TZ });
  const at = (j, h, m = 0) => { const d = new Date(auj + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + j); return new Date(`${d.toISOString().slice(0, 10)}T${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:00+01:00`).toISOString(); };
  const offre = { id: 'o1', titre: 'Escape game « Le Manoir »', genre: 'escape_game', genres: ['escape_game', 'realite_virtuelle'], ambiances: ['girlpower', 'potes', 'romantique'], mode: 'privatise', duree_min: 60, battement_min: 15, prix_cents: 2500, prix_par: 'personne',
    min_personnes: 2, max_personnes: 6, confirmation: 'manuelle', annulation_h: 24, delai_reponse_h: 12, reservable_jours: 60, preavis_h: 2, photos: [], actif: true, description: 'Une heure pour sortir du manoir du comte.', demander_prenoms: true, consignes: 'Arrivez 15 minutes avant.',
    ressources: [{ id: 'r1', nom: 'Le Manoir', capacite: 6, ical_url: 'https://calendar.google.com/calendar/ical/exemple/basic.ics', actif: true }, { id: 'r2', nom: 'La Crypte', capacite: 5, ical_url: '', actif: true }, { id: 'r3', nom: 'Le Labo', capacite: 4, ical_url: '', actif: true }],
    horaires: [1, 2, 3, 4, 5, 6, 7].map((j) => ({ jour: j, debut: j < 6 ? '16:00' : '10:00', fin: '23:00', pas_min: 90 })), fermetures: [{ id: 'fc', ressource_id: null, debut: at(40, 0), fin: at(47, 0), motif: 'ferme', source: 'manuel', note: 'Congés d’hiver' }] };
  const offre2 = { ...offre, id: 'o2', titre: 'Laser game « Néon »', genre: 'laser_game', genres: ['laser_game'], mode: 'places', duree_min: 30, prix_cents: 1200, confirmation: 'immediate', min_personnes: 2, max_personnes: 12,
    ressources: [{ id: 'r9', nom: 'Arène', capacite: 20, actif: true, ical_url: '' }], horaires: [3, 4, 5, 6, 7].map((j) => ({ jour: j, debut: '14:00', fin: '23:00', pas_min: 30 })), fermetures: [] };
  const espace = { entreprise: { id: 'e1', nom: 'Escape Uzès (exemple)', statut: 'valide', fondateur: true, taux_actuel: 0, a_valider: 2, ical_jeton: 'exemple-de-lien-secret', connecteur_demande: 'Bookeo', email: 'contact@exemple.fr', telephone: '06 00 00 00 00',
    site: 'https://exemple.fr', adresse: '3 rue du Duché', commune: 'Uzès', description: 'Trois salles d’escape game au cœur d’Uzès.', siret: '00000000000000', photos: [], notif_mail: true, emails_copie: 'accueil@exemple.fr', facturation: { raison_sociale: 'SAS Exemple' }, role: 'proprietaire' }, offres: [offre, offre2] };
  let n = 0;
  const R = (j, h, m, statut, prenom, p, extra = {}) => ({ id: 'a' + (++n), code: 'TK-' + (482130 + n * 7), statut, debut: at(j, h, m), fin: at(j, h + 1, m), personnes: p, prix_cents: p * 2500, prenom, message: '', groupe: '', participants: [], note_pro: '',
    offre_id: 'o1', offre: offre.titre, ressource_id: 'r1', ressource: 'Le Manoir', repondre_avant: at(0, 23), commission_cents: 0, motif: '', ...extra });
  const resas = [R(0, 17, 30, 'confirmee', 'Hugo', 4), R(0, 19, 0, 'confirmee', 'Léa', 6, { groupe: 'Les Zinzins', participants: ['Léa', 'Max', 'Inès', 'Tom', 'Sarah', 'Noé'], ressource_id: 'r2', ressource: 'La Crypte', note_pro: 'Anniversaire de Max' }),
    R(0, 20, 30, 'confirmee', 'Camille', 2, { ressource_id: 'r3', ressource: 'Le Labo' }), R(0, 22, 0, 'demandee', 'Jules', 5, { groupe: 'Team Rosé', message: 'On sera peut-être 6, c’est possible ?' }),
    R(1, 19, 0, 'demandee', 'Inès', 3, { ressource_id: 'r2', ressource: 'La Crypte' }), R(2, 17, 30, 'confirmee', 'Paul', 4), R(3, 20, 30, 'confirmee', 'Manon', 5, { groupe: 'Les Copines du jeudi' }),
    R(4, 19, 0, 'confirmee', 'Yanis', 6, { ressource_id: 'r3', ressource: 'Le Labo' }), R(-2, 18, 0, 'venue', 'Sarah', 4), R(-3, 20, 0, 'venue', 'Nico', 6, { groupe: 'Les Inséparables' }),
    R(2, 15, 0, 'confirmee', 'Alex', 8, { offre_id: 'o2', offre: offre2.titre, ressource_id: 'r9', ressource: 'Arène', participants: ['Alex', 'Jo', 'Lina', 'Sam', 'Rayan', 'Emma', 'Lou', 'Nils'], prix_cents: 8 * 1200 })];
  const fermes = [{ id: 'f1', offre_id: 'o1', ressource_id: 'r1', debut: at(0, 22, 0), fin: at(0, 23, 0), motif: 'agenda', source: 'ical', note: '' },
    { id: 'f2', offre_id: 'o1', ressource_id: 'r3', debut: at(0, 16, 0), fin: at(0, 17, 0), motif: 'hors_tikette', source: 'manuel', note: 'Famille Martin, 4 pers.' },
    { id: 'f3', offre_id: 'o1', ressource_id: 'r2', debut: at(1, 16, 0), fin: at(1, 19, 0), motif: 'ferme', source: 'manuel', note: 'Maintenance' }];
  const equipe = { membres: [{ user_id: 'u1', email: 'contact@exemple.fr', role: 'proprietaire', moi: true }, { user_id: 'u2', email: 'lucas@exemple.fr', role: 'equipe' }], invitations: ['accueil@exemple.fr'] };
  const releves = [{ mois: at(-32, 12).slice(0, 7), reservations: 41, personnes: 168, ca_cents: 412000, commission_cents: 0 }, { mois: at(-62, 12).slice(0, 7), reservations: 22, personnes: 90, ca_cents: 225000, commission_cents: 0 }];
  const MOTS = ['Julien était génial, on a fini à 2 minutes de la fin !', 'Les énigmes de la Crypte sont vraiment malines.', '', 'Super soirée pour l’anniversaire de Max.', '', 'Un peu court pour le prix, mais le décor est top.', '', 'On reviendra pour le Labo !', '', 'Accueil très chaleureux.', '', ''];
  const TAGS = [['Énigmes au top', 'Super ambiance', 'Accueil au top'], ['Énigmes au top', 'Décor soigné'], ['Super ambiance', 'Idéal entre potes'], ['Super ambiance', 'On y retourne'], ['Parfait pour un 1er date'],
    ['Trop court', 'Décor soigné'], ['Bon rapport prix'], ['On y retourne', 'Énigmes au top'], ['Super ambiance'], ['Accueil au top', 'Facile à trouver'], ['Trop d’attente'], ['Idéal entre potes', 'Super ambiance']];
  const SALLES = [['r1', 'Le Manoir', 5], ['r2', 'La Crypte', 5], ['r1', 'Le Manoir', 5], ['r2', 'La Crypte', 5], ['r1', 'Le Manoir', 4], ['r3', 'Le Labo', 3], ['r2', 'La Crypte', 5], ['r3', 'Le Labo', 4],
    ['r1', 'Le Manoir', 4], ['r2', 'La Crypte', 5], ['r3', 'Le Labo', 4], ['r9', 'Arène', 5]];
  const avis = SALLES.map(([rid, salle, note], i) => ({ id: 'v' + i, note, reaction: note === 5 ? 'adore' : note === 4 ? 'bien' : 'bof', tags: TAGS[i], mot: MOTS[i], reponse: i === 0 ? 'Merci à vous, Julien transmet ses salutations !' : '',
    reponse_le: i === 0 ? at(-1, 10) : null, signale: false, offre: rid === 'r9' ? offre2.titre : offre.titre, salle, ressource_id: rid, debut: at(-2 - i * 2, 20), personnes: 2 + (i * 3) % 5, cree_le: at(-1 - i * 2, 11) }));
  const listeAvis = () => {
    const moy = (l) => Math.round(100 * l.reduce((s, x) => s + x.note, 0) / l.length) / 100;
    const grp = (cle) => Object.values(avis.reduce((m, x) => { (m[x[cle]] = m[x[cle]] || []).push(x); return m; }, {}));
    const comptes = avis.flatMap((x) => x.tags).reduce((m, t) => ((m[t] = (m[t] || 0) + 1), m), {});
    return { nombre: avis.length, moyenne: moy(avis), repartition: [1, 2, 3, 4, 5].map((n) => avis.filter((x) => x.note === n).length), adore: avis.filter((x) => x.reaction === 'adore').length,
      recommandent: Math.round(100 * avis.filter((x) => x.note >= 4).length / avis.length),
      par_offre: grp('offre').map((l) => ({ offre: l[0].offre, nombre: l.length, moyenne: moy(l), adore: l.filter((x) => x.reaction === 'adore').length })).sort((a, b) => b.moyenne - a.moyenne),
      par_salle: grp('salle').map((l) => { const c = l.flatMap((x) => x.tags).reduce((m, t) => ((m[t] = (m[t] || 0) + 1), m), {});
        return { salle: l[0].salle, offre: l[0].offre, nombre: l.length, moyenne: moy(l), adore: l.filter((x) => x.reaction === 'adore').length, tags: Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 3).map((x) => x[0]) }; }).sort((a, b) => b.moyenne - a.moyenne),
      tags: Object.entries(comptes).map(([tag, nombre]) => ({ tag, nombre })).sort((a, b) => b.nombre - a.nombre), avis: [...avis].sort((a, b) => new Date(b.cree_le) - new Date(a.cree_le)) };
  };
  const majAValider = () => { espace.entreprise.a_valider = resas.filter((r) => r.statut === 'demandee').length; };
  const dans = (x, du, au) => new Date(x) >= new Date(du) && new Date(x) < new Date(au);
  const RPC = {
    pro_avis_liste: () => listeAvis(),
    pro_repondre_avis: (a) => { const x = avis.find((y) => y.id === a.p_reservation); x.reponse = a.p_texte; x.reponse_le = new Date().toISOString(); },
    pro_signaler_avis: (a) => { avis.find((y) => y.id === a.p_reservation).signale = true; },
    pro_mon_espace: () => { majAValider(); return espace; }, pro_accepter_invitation: () => false, pro_places_fondateur: () => 47, pro_inscrire: () => ({ ok: true, fondateur: true }),
    pro_reservations_liste: (a) => resas.filter((r) => dans(r.debut, a.p_du, a.p_au)).sort((x, y) => new Date(x.debut) - new Date(y.debut)),
    pro_fermetures_periode: (a) => fermes.filter((f) => new Date(f.fin) > new Date(a.p_du) && new Date(f.debut) < new Date(a.p_au)),
    pro_stats: () => ({ reservations: 38, personnes: 152, ca_cents: 380000, commission_cents: 0, demandes: 41, acceptees: 38, refusees: 3, absents: 1, par_offre: { [offre.titre]: 29, [offre2.titre]: 9 },
      par_jour: Object.fromEntries([...Array(20)].map((_, i) => [at(i - 19, 12).slice(0, 10), (i * 7) % 5 + 1 + (i % 7 > 4 ? 3 : 0)])) }),
    pro_repondre: (a) => { const r = resas.find((x) => x.id === a.p_id); if (!r) return { ok: false };
      r.statut = { accepter: 'confirmee', refuser: 'refusee', annuler: 'annulee_pro', venue: 'venue', absente: 'absente' }[a.p_action]; r.motif = a.p_motif || ''; return { ok: true }; },
    pro_annoter: (a) => { const r = resas.find((x) => x.id === a.p_id); if (r) r.note_pro = a.p_note; },
    pro_fermer: (a) => { fermes.push({ id: 'f' + Date.now(), offre_id: a.p_offre, ressource_id: a.p_ressource, debut: a.p_debut, fin: a.p_fin, motif: a.p_motif, source: 'manuel', note: a.p_note || '' }); },
    pro_fermer_tout: (a) => { espace.offres.forEach((o) => o.fermetures.push({ id: 'fc' + Date.now() + o.id, ressource_id: null, debut: a.p_debut, fin: a.p_fin, motif: 'ferme', source: 'manuel', note: a.p_note })); },
    pro_rouvrir: (a) => { const i = fermes.findIndex((f) => f.id === a.p_fermeture); if (i >= 0) fermes.splice(i, 1); espace.offres.forEach((o) => { o.fermetures = o.fermetures.filter((f) => f.id !== a.p_fermeture); }); },
    pro_enregistrer_offre: (a) => { const p = a.p; const o = espace.offres.find((x) => x.id === p.id);
      const nouv = { ...(o || { fermetures: [] }), ...p, id: p.id || 'o' + Date.now(), genre: (p.genres || [])[0] || '', ressources: p.ressources.map((r, i) => ({ id: r.id || 'r' + Date.now() + i, actif: true, ...r })) };
      if (o) Object.assign(o, nouv); else espace.offres.push(nouv); return nouv.id; },
    pro_supprimer_offre: (a) => { espace.offres = espace.offres.filter((o) => o.id !== a.p_offre); },
    pro_modifier_entreprise: (a) => { Object.assign(espace.entreprise, a.p); },
    pro_equipe: () => equipe, pro_inviter: (a) => { equipe.invitations.push(a.p_email); return { ok: true, ajoute: false }; },
    pro_retirer_membre: (a) => { equipe.membres = equipe.membres.filter((m) => m.user_id !== a.p_user); equipe.invitations = equipe.invitations.filter((i) => i !== a.p_email); },
    pro_releves: () => releves, pro_quitter: () => { espace.entreprise.statut = 'quitte'; return 0; },
  };
  let connecte = location.pathname.includes('/espace/');
  const user = { id: 'u1', email: 'contact@exemple.fr' };
  const ok = (data) => Promise.resolve({ data, error: null });
  const fichiers = {};
  const client = {
    rpc: (nom, args) => ok(RPC[nom] ? JSON.parse(JSON.stringify(RPC[nom](args || {}) ?? null)) : null),
    auth: {
      getSession: () => ok({ session: connecte ? { user } : null }), getUser: () => ok({ user }),
      signInWithOtp: () => ok({}), verifyOtp: () => { connecte = true; return ok({ session: { user } }); }, signOut: () => { connecte = false; return ok({}); }, updateUser: () => ok({ user }),
      mfa: { getAuthenticatorAssuranceLevel: () => ok({ currentLevel: 'aal1', nextLevel: 'aal1' }), listFactors: () => ok({ totp: [] }), unenroll: () => ok({}), challengeAndVerify: () => ok({}),
        enroll: () => ok({ id: 'f1', totp: { secret: 'EXEMPLE DEMO CODE', qr_code: 'data:image/svg+xml;utf8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" fill="#fff"/><path d="M1 1h3v3H1zM6 1h3v3H6zM1 6h3v3H1zM5 5h1v1H5zM7 6h2v1H7zM6 8h1v1H6z" fill="#1E1433"/></svg>') } }) },
    },
    storage: { from: () => ({ upload: (chemin, f) => { fichiers[chemin] = URL.createObjectURL(f); return ok({}); }, getPublicUrl: (chemin) => ({ data: { publicUrl: fichiers[chemin] } }) }) },
  };
  window.supabase = { createClient: () => client };
  document.addEventListener('DOMContentLoaded', () => {
    const b = document.createElement('div');
    b.textContent = 'Démonstration · données d’exemple, rien n’est envoyé ni enregistré';
    b.style.cssText = 'position:fixed;top:0;left:50%;transform:translateX(-50%);z-index:99;background:#FFD166;color:#1E1433;font:700 12px "DM Sans",sans-serif;padding:5px 14px;border-radius:0 0 10px 10px';
    document.body.appendChild(b);
  });
})();
