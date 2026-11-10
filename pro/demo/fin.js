// Démo temporaire de l'espace pro (demande de Greg, 11 nov. 2026) : ne marche plus après FIN.
(function () {
  const FIN = Date.parse('2026-11-11T00:49:47Z');
  const heure = new Date(FIN).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Paris' });
  const fini = Date.now() > FIN;
  if (fini) window.stop && window.stop();
  document.addEventListener('DOMContentLoaded', () => {
    if (fini) {
      document.body.innerHTML = '<div style="font-family:system-ui;max-width:420px;margin:120px auto;text-align:center;color:#F7F1FF;background:#1E1433;padding:32px;border-radius:20px"><h1 style="font-size:24px">Démo terminée</h1><p>Cette démonstration de l’espace pro n’est plus disponible.</p><p><a style="color:#FFD166" href="/pro/">Retour à tikette.fr/pro</a></p></div>';
      document.body.style.background = '#1E1433';
      return;
    }
    const b = document.createElement('div');
    b.textContent = 'DÉMO · données d’exemple, rien n’est envoyé ni enregistré · disponible jusqu’à ' + heure;
    b.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:9999;background:#FFD166;color:#1E1433;font:700 12.5px system-ui;text-align:center;padding:6px 10px';
    document.body.appendChild(b);
  });
})();
