// Refuse d'être affichée dans le cadre d'un autre site (piège au clic). Les pages du même site restent permises.
(function () {
  if (window.top === window.self) return;
  try { if (window.top.location.origin === window.location.origin) return; } catch (e) { /* autre site */ }
  document.documentElement.innerHTML = '';
  window.top.location = window.location.href;
})();
