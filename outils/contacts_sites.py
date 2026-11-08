"""Complète la liste des prospects : cherche l'e-mail et le téléphone publiés sur le site de chaque entreprise
(page d'accueil, puis une page « contact » si elle existe). Utilisé seulement par le workflow prospects.yml.

Usage : python3 outils/contacts_sites.py prospects.csv sortie.csv
"""
import concurrent.futures as cf
import csv
import re
import sys
import urllib.parse
import urllib.request

MAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}', re.I)
TEL = re.compile(r'(?:\+33[\s.]?|0)[1-9](?:[\s.-]?\d{2}){4}')
EXCLURE = re.compile(r'(example|exemple|sentry|wixpress|domain\.|\.png|\.jpg|\.webp|\.gif|@2x|godaddy|jquery|wordpress|mysite|votre|your|email@|nom@|prenom)', re.I)
ENTETES = {'User-Agent': 'Mozilla/5.0 (compatible; TiketteBot/1.0; +https://tikette.fr)'}


def lire(url):
    try:
        req = urllib.request.Request(url, headers=ENTETES)
        with urllib.request.urlopen(req, timeout=8) as r:
            if 'html' not in (r.headers.get('Content-Type') or 'html'):
                return '', url
            return r.read(600000).decode('utf-8', 'ignore'), r.geturl()
    except Exception:
        return '', url


def trouver(site):
    if not site or 'guidap' in site or 'book.' in site:
        return '', ''
    html, final = lire(site)
    mails, tels = set(), set()

    def extraire(h):
        h2 = h.replace('&#64;', '@').replace('[at]', '@').replace('(at)', '@')
        for m in re.findall(r'mailto:([^"\'?>\s]+)', h2, re.I) + MAIL.findall(h2):
            m = urllib.parse.unquote(m).strip().lower().rstrip('.')
            if MAIL.fullmatch(m) and not EXCLURE.search(m):
                mails.add(m)
        for t in re.findall(r'tel:([+\d\s.-]{9,})', h2, re.I) + TEL.findall(h2):
            t = re.sub(r'[^\d+]', '', t)
            if len(t) >= 10:
                tels.add(t)
    extraire(html)
    if not mails and html:
        for lien in re.findall(r'href="([^"]*(?:contact|nous-contacter|infos|acces)[^"]*)"', html, re.I)[:2]:
            h, _ = lire(urllib.parse.urljoin(final, lien))
            extraire(h)
            if mails:
                break
    return ' / '.join(sorted(mails)[:2]), ' / '.join(sorted(tels)[:2])


def main():
    with open(sys.argv[1], encoding='utf-8-sig') as f:
        lignes = list(csv.DictReader(f, delimiter=';'))
    with cf.ThreadPoolExecutor(24) as ex:
        res = list(ex.map(lambda l: trouver(l['Site']), lignes))
    for l, (m, t) in zip(lignes, res):
        l['E-mail'] = l['E-mail'] or m
        l['Téléphone'] = l['Téléphone'] or t
    with open(sys.argv[2], 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=';')
        w.writeheader()
        w.writerows(lignes)
    import base64, gzip
    print(sum(1 for l in lignes if l['E-mail']), 'e-mails,', sum(1 for l in lignes if l['Téléphone']), 'téléphones sur', len(lignes))
    print('DEBUT_CSV')
    print(base64.b64encode(gzip.compress(open(sys.argv[2], 'rb').read())).decode())
    print('FIN_CSV')


if __name__ == '__main__':
    main()
