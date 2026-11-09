// tikette.fr/pro : calcul, places de fondateur, inscription (SIRET et adresse vérifiés, code par e-mail).
const sb = window.supabase.createClient('https://mmoyrhyimcalnztwpydi.supabase.co', 'sb_publishable_SSawNJhqUZUxxKpzIds7kQ_80hU2NSH',
  { auth: { persistSession: true, storageKey: 'tikette-pro' } });
const $ = (s) => document.querySelector(s);
const euros = (n) => Math.round(n).toLocaleString('fr-FR') + ' €';

// ── Calcul ──
function calculer() {
  const ca = (+$('#c-prix').value || 0) * (+$('#c-pers').value || 0) * (+$('#c-nb').value || 0);
  $('#r-ca').textContent = euros(ca); $('#r-com').textContent = euros(ca * 0.1);
  $('#r-garde').textContent = euros(ca * 0.9); $('#r-autre').textContent = euros(ca * 0.75);
}
['#c-prix', '#c-pers', '#c-nb'].forEach((id) => $(id).addEventListener('input', calculer));

// ── Places de fondateur ──
sb.rpc('pro_places_fondateur').then(({ data }) => {
  if (typeof data === 'number') $('#reste').textContent = data ? `il en reste ${data}` : 'toutes prises';
});

// ── Types d'activité ──
const champTypes = ChampTypes($('#i-types'), { max: 8 });

// ── SIRET : clé de contrôle puis annuaire officiel (recherche-entreprises.api.gouv.fr, gratuit, sans clé) ──
let siretOk = null; // null = pas vérifié, false = faux, objet = trouvé
function cleLuhn(n) {
  if (n.startsWith('356000000')) return [...n].reduce((s, c) => s + +c, 0) % 5 === 0; // La Poste
  let s = 0; for (let i = 0; i < 14; i++) { let d = +n[13 - i]; if (i % 2) { d *= 2; if (d > 9) d -= 9; } s += d; } return s % 10 === 0;
}
async function verifierSiret() {
  const n = $('#i-siret').value.replace(/\D/g, ''); const a = $('#a-siret');
  siretOk = null; a.className = 'aide';
  if (!n) { a.textContent = 'Vérifié automatiquement dans l’annuaire officiel des entreprises.'; return; }
  if (n.length !== 14 || !cleLuhn(n)) { siretOk = false; a.className = 'aide ko'; a.textContent = 'Ce n’est pas un SIRET valide (14 chiffres).'; return; }
  a.textContent = 'Vérification…';
  try {
    const r = await fetch(`https://recherche-entreprises.api.gouv.fr/search?q=${n}&per_page=1`).then((x) => x.json());
    const ent = r.results?.[0];
    const etab = ent && ([...(ent.matching_etablissements || []), ent.siege].find((e) => e?.siret === n));
    if (!etab) { siretOk = false; a.className = 'aide ko'; a.textContent = 'SIRET introuvable dans l’annuaire.'; return; }
    if (etab.etat_administratif === 'F') { siretOk = false; a.className = 'aide ko'; a.textContent = 'Cet établissement est fermé.'; return; }
    siretOk = { nom: ent.nom_complet, adresse: etab.adresse };
    a.className = 'aide ok';
    a.textContent = /NON-DIFFUSIBLE/.test(ent.nom_complet || '') ? '✓ SIRET reconnu' : `✓ ${ent.nom_complet}${etab.libelle_commune ? ' · ' + etab.libelle_commune : ''}`;
    if (!$('#i-adr').value && etab.adresse && !/NON-DIFFUSIBLE/.test(etab.adresse)) { $('#i-adr').value = etab.adresse; chercherAdresse(); }
  } catch { siretOk = 'hors-ligne'; a.className = 'aide'; a.textContent = 'Annuaire injoignable : on vérifiera à la main.'; }
}
$('#i-siret').addEventListener('change', verifierSiret);
$('#i-siret').addEventListener('input', () => { if ($('#i-siret').value.replace(/\D/g, '').length === 14) verifierSiret(); });

// ── Adresse : Base Adresse Nationale (Géoplateforme IGN, gratuite) ──
let adresse = null, minuteur;
function chercherAdresse() {
  adresse = null; clearTimeout(minuteur);
  const q = $('#i-adr').value.trim(); const p = $('#propos');
  $('#a-adr').className = 'aide'; $('#a-adr').textContent = 'Choisissez l’adresse dans la liste : c’est là que Tikette envoie les clients.';
  if (q.length < 4) { p.classList.add('cache'); return; }
  minuteur = setTimeout(async () => {
    try {
      const r = await fetch(`https://data.geopf.fr/geocodage/search?q=${encodeURIComponent(q)}&limit=5`).then((x) => x.json());
      const f = (r.features || []).filter((x) => x.properties?.postcode);
      if (!f.length) { p.classList.add('cache'); $('#a-adr').className = 'aide ko'; $('#a-adr').textContent = 'Adresse introuvable : essayez avec le code postal.'; return; }
      p.innerHTML = ''; f.forEach((x) => {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = x.properties.label;
        b.onclick = () => {
          const pr = x.properties;
          adresse = { adresse: pr.name || pr.label, commune: pr.city, code_postal: pr.postcode, lat: x.geometry.coordinates[1], lon: x.geometry.coordinates[0] };
          $('#i-adr').value = pr.label; p.classList.add('cache');
          $('#a-adr').className = 'aide ok'; $('#a-adr').textContent = '✓ Adresse reconnue';
        };
        p.appendChild(b);
      });
      p.classList.remove('cache');
    } catch { $('#a-adr').className = 'aide ko'; $('#a-adr').textContent = 'Recherche d’adresse indisponible, réessayez.'; }
  }, 350);
}
$('#i-adr').addEventListener('input', chercherAdresse);
document.addEventListener('click', (e) => { if (!e.target.closest('#propos, #i-adr')) $('#propos').classList.add('cache'); });

// ── Inscription ──
let infos = null;
let champ = { valeurs: () => [], noms: () => [] }; champTypes.then((c) => { champ = c; });
function lireFormulaire() {
  const nom = $('#i-nom').value.trim(), email = $('#i-mail').value.trim().toLowerCase();
  let site = $('#i-site').value.trim(); if (site && !/^https?:\/\//.test(site)) site = 'https://' + site;
  if (nom.length < 2) return 'Indiquez le nom de l’activité.';
  if (siretOk === false) return 'Le SIRET n’est pas valide (laissez vide si vous n’en avez pas encore).';
  if (!adresse) return 'Choisissez l’adresse dans la liste proposée.';
  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(email)) return 'L’adresse e-mail ne semble pas valide.';
  if (!champ.valeurs().length) return 'Choisissez au moins un type d’activité.';
  if (!$('#i-ok').checked) return 'Cochez la case des conditions partenaires.';
  infos = { nom, siret: $('#i-siret').value.replace(/\D/g, ''), activite: champ.noms().join(', '), genres: champ.valeurs(), ...adresse, email, telephone: $('#i-tel').value.trim(), site };
  return '';
}
async function inscrire() {
  const { data, error } = await sb.rpc('pro_inscrire', { p: infos });
  if (error) throw error;
  try { localStorage.removeItem('tikette-pro-inscription'); } catch {}
  location.href = '/pro/espace/' + (data?.fondateur ? '#accueil' : '');
}
$('#f-insc').addEventListener('submit', async (e) => {
  e.preventDefault(); const err = lireFormulaire(); $('#i-err').textContent = err; if (err) return;
  $('#i-go').disabled = true;
  try {
    const { data: s } = await sb.auth.getSession();
    if (s.session) { await inscrire(); return; } // déjà connecté (ex. depuis l'espace pro)
    try { localStorage.setItem('tikette-pro-inscription', JSON.stringify(infos)); } catch {}
    const { error } = await sb.auth.signInWithOtp({ email: infos.email, options: { shouldCreateUser: true } });
    if (error) throw error;
    $('#c-mail').textContent = infos.email; $('#f-insc').classList.add('cache'); $('#f-code').classList.remove('cache'); $('#c-code').focus();
  } catch (x) { $('#i-err').textContent = /rate|seconds/i.test(x.message) ? 'Patientez une minute avant de redemander un code.' : 'Impossible pour l’instant : ' + x.message; }
  $('#i-go').disabled = false;
});
$('#f-code').addEventListener('submit', async (e) => {
  e.preventDefault(); $('#c-err').textContent = '';
  const { error } = await sb.auth.verifyOtp({ email: infos.email, token: $('#c-code').value.trim(), type: 'email' });
  if (error) { $('#c-err').textContent = 'Code incorrect ou expiré.'; return; }
  try { await inscrire(); } catch (x) { $('#c-err').textContent = x.message; }
});
$('#c-retour').addEventListener('click', () => { $('#f-code').classList.add('cache'); $('#f-insc').classList.remove('cache'); });

// Venu de l'espace pro sans entreprise : reprise des informations tapées avant.
try { const t = JSON.parse(localStorage.getItem('tikette-pro-inscription') || 'null'); if (t) { $('#i-nom').value = t.nom || ''; $('#i-mail').value = t.email || ''; } } catch {}
