// Champ « types d'activité » : on tape le début d'un type ou un mot de son activité, on choisit, on recommence.
// Liste dans /pro/types-activite.json (fabriquée par outils/types-activite.py du dépôt AppliDates).
(function () {
  let catalogue = null;
  const charger = () => catalogue || (catalogue = fetch(window.TYPES_URL || '/pro/types-activite.json').then((r) => r.json()).catch(() => []));
  const norm = (t) => String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, ' ');
  const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const POPULAIRES = ['escape_game', 'laser_game', 'karting', 'bowling', 'canoe', 'accrobranche', 'atelier_cuisine', 'domaine', 'spa', 'restaurant', 'bar_cocktails', 'montgolfiere'];
  function chercher(liste, q, deja) {
    const mots = norm(q).split(/\s+/).filter(Boolean);
    const libres = liste.filter((t) => !deja.includes(t.id));
    if (!mots.length) return POPULAIRES.map((id) => libres.find((t) => t.id === id)).filter(Boolean);
    return libres.map((t) => {
      const nom = norm(t.nom), tout = (nom + ' ' + norm(t.mots)).split(/[\s,()\-/]+/);
      let score = 0;
      for (const m of mots) {
        if (tout.some((w) => w.startsWith(m))) score += nom.startsWith(m) ? 3 : nom.split(/[\s,()\-/]+/).some((w) => w.startsWith(m)) ? 2 : 1;
        else if (nom.includes(m)) score += 1;
        else return null;
      }
      return { t, score };
    }).filter(Boolean).sort((a, b) => b.score - a.score || a.t.nom.localeCompare(b.t.nom)).slice(0, 8).map((x) => x.t);
  }
  window.ChampTypes = async function (racine, { valeurs = [], max = 8, surChange = () => {}, placeholder = 'Ex. escape, canoë, cocktails, poterie…' } = {}) {
    const liste = await charger();
    let choisis = valeurs.filter((v) => liste.some((t) => t.id === v)), actif = 0, propositions = [];
    racine.classList.add('ct');
    racine.innerHTML = `<div class="ct-puces"></div><div class="ct-saisie"><input type="text" autocomplete="off" placeholder="${esc(placeholder)}" aria-label="Chercher un type d’activité"><div class="ct-liste" hidden></div></div><div class="ct-aide"></div>`;
    const puces = racine.querySelector('.ct-puces'), champ = racine.querySelector('input'), boite = racine.querySelector('.ct-liste'), aide = racine.querySelector('.ct-aide');
    const nom = (id) => liste.find((t) => t.id === id)?.nom || id;
    const dessinerPuces = () => {
      puces.innerHTML = choisis.map((id) => `<span class="ct-puce">${esc(nom(id))}<button type="button" data-retirer="${id}" aria-label="Retirer ${esc(nom(id))}">×</button></span>`).join('');
      puces.querySelectorAll('[data-retirer]').forEach((b) => b.onclick = () => { choisis = choisis.filter((x) => x !== b.dataset.retirer); dessinerPuces(); surChange(choisis); champ.focus(); });
      aide.textContent = choisis.length >= max ? `${max} types au plus.` : choisis.length ? 'Ajoutez-en un autre si besoin.' : '';
      champ.disabled = choisis.length >= max;
    };
    const fermer = () => { boite.hidden = true; };
    const ouvrir = () => {
      propositions = chercher(liste, champ.value, choisis); actif = 0;
      boite.innerHTML = (champ.value.trim() ? '' : '<div class="ct-titre">Les plus courants</div>')
        + (propositions.map((t, i) => `<button type="button" class="ct-item${i === 0 ? ' on' : ''}" data-i="${i}">${esc(t.nom)}</button>`).join('')
        || `<div class="ct-vide">Rien trouvé pour « ${esc(champ.value)} ». Essayez un autre mot, ou écrivez-nous : contact@tikette.fr</div>`);
      boite.querySelectorAll('[data-i]').forEach((b) => b.onmousedown = (e) => { e.preventDefault(); ajouter(propositions[+b.dataset.i]); });
      boite.hidden = false;
    };
    const ajouter = (t) => { if (!t || choisis.length >= max) return; choisis.push(t.id); champ.value = ''; dessinerPuces(); surChange(choisis); ouvrir(); };
    champ.addEventListener('input', ouvrir); champ.addEventListener('focus', ouvrir); champ.addEventListener('blur', () => setTimeout(fermer, 120));
    champ.addEventListener('keydown', (e) => {
      const items = boite.querySelectorAll('.ct-item');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (!items.length) return; actif = (actif + (e.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length; items.forEach((x, i) => x.classList.toggle('on', i === actif)); items[actif].scrollIntoView({ block: 'nearest' }); }
      else if (e.key === 'Enter') { e.preventDefault(); ajouter(propositions[actif]); }
      else if (e.key === 'Escape') fermer();
      else if (e.key === 'Backspace' && !champ.value && choisis.length) { choisis.pop(); dessinerPuces(); surChange(choisis); }
    });
    dessinerPuces();
    return { valeurs: () => [...choisis], noms: () => choisis.map(nom) };
  };
  window.nomsTypes = async (ids) => { const l = await charger(); return (ids || []).map((id) => l.find((t) => t.id === id)?.nom).filter(Boolean); };
})();
