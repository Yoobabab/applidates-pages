// tikette.fr/pro : animations de la page (aucune donnée envoyée).
(function () {
  const $ = (s) => document.querySelector(s), $$ = (s) => [...document.querySelectorAll(s)];
  const calme = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // Barre du haut qui se colle, bouton en bas sur téléphone.
  const nav = $('#nav'), bas = $('#colle-bas'), insc = $('#inscription');
  addEventListener('scroll', () => {
    nav.classList.toggle('colle', scrollY > 40);
    const r = insc.getBoundingClientRect();
    bas.classList.toggle('on', scrollY > 600 && (r.top > innerHeight || r.bottom < 0));
  }, { passive: true });

  // Mot qui change dans le titre.
  const mots = $$('#tourne span'); let im = 0;
  if (!calme) setInterval(() => {
    const a = mots[im]; im = (im + 1) % mots.length; const b = mots[im];
    a.className = 'avant'; b.className = '';
    setTimeout(() => { a.className = 'apres'; }, 600);
  }, 2600);

  // Petites bulles autour de Tikette.
  const BULLES = [
    ['Nouvelle réservation', 'Les Zinzins · 4 pers. · samedi 20:30'],
    ['Avis 5 étoiles', '« Énigmes au top, on revient ! »'],
    ['Réservation confirmée', 'Léa · 2 pers. · vendredi 19:00'],
    ['Nouvelle réservation', 'EVJF Camille · 8 pers. · samedi 15:00'],
    ['Avis 5 étoiles', '« Parfait pour un 1er date »'],
    ['Nouvelle réservation', 'Team Rosé · 5 pers. · dimanche 16:30'],
  ];
  let ib = 0;
  const bulle = (el) => { const [t, d] = BULLES[ib++ % BULLES.length]; el.classList.remove('on'); setTimeout(() => { el.innerHTML = `<b><i></i>${esc(t)}</b>${esc(d)}`; el.classList.add('on'); }, 450); };
  bulle($('#bulle1')); setTimeout(() => bulle($('#bulle2')), 1500);
  if (!calme) { setInterval(() => bulle($('#bulle1')), 6000); setTimeout(() => setInterval(() => bulle($('#bulle2')), 6000), 3000); }

  // Compte à rebours jusqu'à la sortie (14 décembre 2026, 9 h à Paris).
  const sortie = new Date('2026-12-14T09:00:00+01:00').getTime();
  const deux = (n) => String(n).padStart(2, '0');
  const tic = () => {
    let s = Math.max(0, Math.floor((sortie - Date.now()) / 1000));
    if (!s) { $('.compte .lbl').innerHTML = 'Tikette est sorti !<small>Les clients réservent déjà : inscrivez-vous.</small>'; }
    $('#cj').textContent = Math.floor(s / 86400); $('#ch').textContent = deux(Math.floor(s % 86400 / 3600));
    $('#cm').textContent = deux(Math.floor(s % 3600 / 60)); $('#cs').textContent = deux(s % 60);
  };
  if ($('#cj')) { tic(); setInterval(tic, 1000); }

  // Bandeau des activités qui défile.
  const A = ['Escape game', 'Canoë-kayak', 'Karting', 'Atelier cuisine', 'Dégustation de vins', 'Laser game', 'Montgolfière', 'Spa et hammam', 'Poterie', 'Bowling', 'Accrobranche', 'Réalité virtuelle',
    'Balade à cheval', 'Cours de cocktails', 'Paddle', 'Visite de domaine', 'Quiz room', 'Lancer de hache', 'Atelier parfum', 'Paintball', 'Plongée', 'Stand de tir', 'Cabaret', 'Restaurant'];
  const remplir = (el, l) => { el.innerHTML = [...l, ...l].map((t, i) => `<span class="${i % 5 === 2 ? 'o' : ''}">${esc(t)}</span>`).join(''); };
  remplir($('#rail1'), A.slice(0, 12)); remplir($('#rail2'), A.slice(12));

  // Compteurs qui montent.
  const compter = (el) => {
    const fin = +el.dataset.compte, suf = el.dataset.suffixe || '', t0 = performance.now(), duree = 1100;
    if (calme || !fin) { el.textContent = fin + suf; return; }
    const pas = (t) => { const p = Math.min(1, (t - t0) / duree), v = Math.round(fin * (1 - Math.pow(1 - p, 3))); el.textContent = v + suf; if (p < 1) requestAnimationFrame(pas); };
    requestAnimationFrame(pas);
  };

  // Téléphones : le programme, le choix de l'heure, la confirmation. En boucle tant qu'on les voit.
  let telMinuterie = null;
  const jouerTel = () => {
    const tels = $$('#telephones .tel'), cr = $$('#cren span'), d = $('#doigt'), g = $('#gbtn');
    const etapes = [
      () => { tels.forEach((t) => t.classList.remove('joue')); cr.forEach((c) => c.classList.remove('on')); d.classList.remove('on'); },
      () => tels[0].classList.add('joue'),
      () => { d.style.left = '40%'; d.style.top = '33%'; d.classList.add('on'); },
      () => cr[1].classList.add('on'),
      () => { d.style.left = '48%'; d.style.top = '76%'; },
      () => { g.classList.add('appui'); setTimeout(() => g.classList.remove('appui'), 180); },
      () => { d.classList.remove('on'); tels[2].classList.add('joue'); },
    ];
    let i = 0; clearInterval(telMinuterie);
    etapes[0]();
    telMinuterie = setInterval(() => { i = (i + 1) % (etapes.length + 3); if (i < etapes.length) etapes[i](); }, 900);
  };

  // Aperçu de l'espace pro : onglets qui tournent, réservations qui arrivent.
  const ong = $$('#onglets-ap button'), pans = $$('.ecran-pro .panneau'), menus = $$('.ecran-pro .menu i');
  let ip = 0, apMinuterie = null;
  const montrer = (n) => {
    ip = n; ong.forEach((b, i) => b.classList.toggle('on', i === n)); pans.forEach((p, i) => p.classList.toggle('on', i === n));
    menus.forEach((m, i) => m.classList.toggle('on', i === [0, 1, 3][n]));
    ong[n].querySelector('i').style.animation = 'none'; void ong[n].offsetWidth; ong[n].querySelector('i').style.animation = '';
    if (n === 0) flux();
  };
  ong.forEach((b) => b.onclick = () => { montrer(+b.dataset.p); clearInterval(apMinuterie); apMinuterie = setInterval(() => montrer((ip + 1) % 3), 6000); });
  const RESAS = [
    ['20:30', 'Les Zinzins', 'Le Manoir · 4 pers. · « On fête l’anniversaire de Max ! »', 'att', 'À valider'],
    ['18:00', 'Léa', 'La Crypte · 2 pers.', 'ok', 'Confirmée'],
    ['15:00', 'EVJF Camille', 'Le Labo · 6 pers. · Camille, Inès, Sarah, Jade…', 'att', 'À valider'],
    ['21:30', 'Team Rosé', 'Le Manoir · 5 pers.', 'ok', 'Confirmée'],
  ];
  let fluxMinuterie = null;
  const flux = () => {
    const el = $('#flux'); el.innerHTML = ''; let k = 0; clearInterval(fluxMinuterie);
    const ajouter = () => {
      const [h, n, d, c, t] = RESAS[k++ % RESAS.length];
      el.insertAdjacentHTML('afterbegin', `<div class="ligne-r neuve"><span class="h">${h}</span><div><b>${esc(n)}</b><small>${esc(d)}</small></div><span class="${c}">${t}</span></div>`);
      while (el.children.length > 4) el.lastElementChild.remove();
    };
    ajouter(); ajouter(); fluxMinuterie = setInterval(ajouter, 1700);
  };

  // Apparitions au défilement.
  const vu = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('vu'); vu.unobserve(e.target);
    e.target.querySelectorAll('[data-compte]').forEach(compter);
    e.target.querySelectorAll('#barres .b i').forEach((i) => { i.style.width = i.style.getPropertyValue('--w'); });
  }), { threshold: 0.18 });
  $$('.apparait').forEach((el) => vu.observe(el));
  if (calme) $$('.apparait').forEach((el) => { el.classList.add('vu'); el.querySelectorAll('[data-compte]').forEach(compter); });

  const visible = (el, oui, non) => new IntersectionObserver(([e]) => (e.isIntersecting ? oui() : non()), { threshold: 0.3 }).observe(el);
  if (!calme) {
    visible($('#telephones'), jouerTel, () => clearInterval(telMinuterie));
    visible($('.ecran-pro'), () => { montrer(ip); clearInterval(apMinuterie); apMinuterie = setInterval(() => montrer((ip + 1) % 3), 6000); },
      () => { clearInterval(apMinuterie); clearInterval(fluxMinuterie); });
  } else { $$('#telephones .tel').forEach((t) => t.classList.add('joue')); $$('#cren span')[1].classList.add('on'); flux(); clearInterval(fluxMinuterie); }

  // Calcul : curseurs remplis et chiffres animés.
  window.animerNombre = (el, fin, format) => {
    const debut = +(el.dataset.v || fin); el.dataset.v = fin;
    if (calme || debut === fin) { el.textContent = format(fin); return; }
    const t0 = performance.now();
    const pas = (t) => { const p = Math.min(1, (t - t0) / 380); el.textContent = format(debut + (fin - debut) * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(pas); };
    requestAnimationFrame(pas);
  };
  $$('input[type=range]').forEach((r) => { const maj = () => r.style.setProperty('--p', (100 * (r.value - r.min) / (r.max - r.min)) + '%'); r.addEventListener('input', maj); maj(); });
})();
