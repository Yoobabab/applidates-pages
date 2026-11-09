#!/usr/bin/env python3
"""Règles de sécurité des pages (Content-Security-Policy) : à relancer après CHAQUE modification d'une page.

    python3 outils/securite-pages.py <dossier>

Pour chaque fichier .html du dossier : calcule l'empreinte (sha256) de chaque <script> écrit dans la page
et met à jour la balise <meta http-equiv="Content-Security-Policy"> juste après <meta charset>.
Seuls ces scripts-là et ceux du site lui-même peuvent s'exécuter : un script glissé par un pirate
(ou une bibliothèque modifiée sur un site extérieur) est bloqué par le navigateur.
Même outil dans les dépôts EggNotFoundGestion et applidates-pages (garder les deux identiques).
"""
import base64, hashlib, pathlib, re, sys

SUPABASE = 'https://mmoyrhyimcalnztwpydi.supabase.co'
CONNEXIONS = [SUPABASE, SUPABASE.replace('https://', 'wss://'), 'https://api.github.com', 'https://raw.githubusercontent.com',
              'https://recherche-entreprises.api.gouv.fr', 'https://data.geopf.fr']
SCRIPT = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', re.S | re.I)
ANCIENNE = re.compile(r'\s*<meta http-equiv="Content-Security-Policy"[^>]*>', re.I)
REFERRER = '<meta name="referrer" content="strict-origin-when-cross-origin">'


def regles(html: str) -> str:
    empreintes = ["'sha256-%s'" % base64.b64encode(hashlib.sha256(s.encode('utf-8')).digest()).decode() for s in SCRIPT.findall(html)]
    a_des_scripts = bool(empreintes) or re.search(r'<script[^>]*\bsrc=', html, re.I)
    return '; '.join([
        "default-src 'self'",
        "script-src " + (' '.join(["'self'"] + empreintes) if a_des_scripts else "'none'"),
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: blob: https:",
        "connect-src 'self' " + ' '.join(CONNEXIONS),
        "frame-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
    ])


def traiter(fichier: pathlib.Path) -> bool:
    html = fichier.read_text(encoding='utf-8')
    propre = ANCIENNE.sub('', html)
    if REFERRER not in propre:
        propre = re.sub(r'(<meta charset="[^"]*">)', r'\1\n' + REFERRER, propre, count=1, flags=re.I)
    meta = '<meta http-equiv="Content-Security-Policy" content="%s">' % regles(propre)
    nouveau, n = re.subn(r'(<meta charset="[^"]*">)', lambda m: m.group(1) + '\n' + meta, propre, count=1, flags=re.I)
    if not n:
        print('  ⚠ pas de <meta charset> :', fichier); return False
    if nouveau != html:
        fichier.write_text(nouveau, encoding='utf-8'); return True
    return False


if __name__ == '__main__':
    racine = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
    changes = [str(f) for f in sorted(racine.rglob('*.html')) if '.git' not in f.parts and 'node_modules' not in f.parts and traiter(f)]
    print(f'{len(changes)} page(s) mise(s) à jour' + (' : ' + ', '.join(changes) if changes else ''))
