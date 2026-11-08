"""Liste d'entreprises à contacter pour l'espace pro de Tikette (lancement manuel, workflow prospects.yml).

Lit les fichiers DATAtourisme (place + product, licence ouverte Etalab 2.0), garde les activités
privées et réservables (pas les musées municipaux, parcs, sites naturels…) dans les départements
choisis et écrit un CSV : nom, activité, commune, code postal, e-mail, téléphone, site, adresse.
Le fichier est seulement envoyé comme « artefact » du workflow (gardé 1 jour), jamais publié dans le dépôt.

Usage : python3 outils/prospects.py sortie.csv "30,84,13,34" place.csv [product.csv …]
"""
import csv
import re
import sys

sys.path.insert(0, 'outils')
from datatourisme import genre, nettoyer, premier_lien, sans_accents  # noqa: E402

ACTIVITES = {
    'vr': 'Réalité virtuelle', 'hache': 'Lancer de hache', 'tir': 'Stand de tir', 'soufflerie': 'Chute libre indoor',
    'velorail': 'Vélorail', 'usine': "Visite d'atelier / savoir-faire", 'insolite': 'Activité insolite', 'tir_arc': "Tir à l'arc",
    'labyrinthe': 'Labyrinthe', 'cabaret': 'Cabaret / dîner-spectacle', 'billard': 'Billard / bar à jeux',
    'brasserie': 'Brasserie / distillerie', 'grotte': 'Grotte', 'observatoire': 'Observatoire', 'ferme': 'Ferme / cueillette',
    'aerien': 'Montgolfière / parapente / ULM', 'eaux_vives': 'Rafting / canyoning', 'canoe': 'Canoë / kayak / paddle',
    'voile': 'Voile / plongée / nautique', 'bateau': 'Bateau / croisière', 'climbing_adventure': 'Accrobranche / via ferrata',
    'climbing': 'Escalade', 'escape': 'Escape game', 'laser_tag': 'Laser game', 'paintball': 'Paintball', 'karting': 'Karting',
    'bowling_alley': 'Bowling', 'ice_rink': 'Patinoire', 'trampoline_park': 'Trampoline', 'miniature_golf': 'Mini-golf',
    'golf': 'Golf', 'horse_riding': 'Équitation', 'velo': 'Location de vélos', 'theme_park': "Parc d'attractions",
    'water_park': 'Parc aquatique', 'zoo': 'Parc animalier', 'aquarium': 'Aquarium', 'planetarium': 'Planétarium',
    'bains': 'Spa / bien-être', 'atelier': 'Atelier / cours', 'winery': 'Domaine / dégustation',
}
EXEMPLES = []
MAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
TEL = re.compile(r'(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}')


def main():
    sortie, deps = sys.argv[1], [d.strip() for d in sys.argv[2].split(',')]
    lignes, vus = [], set()
    global EXEMPLES
    csv.field_size_limit(10**9)
    for chemin in sys.argv[3:]:
        with open(chemin, encoding='utf-8', newline='') as f:
            for l in csv.DictReader(f):
                cp, _, commune = (l.get('Code_postal_et_commune') or '').partition('#')
                cp = cp.strip()
                if not any(cp.startswith(d) for d in deps):
                    continue
                nom = nettoyer(l.get('Nom_du_POI'), 90)
                g = genre(nom, l.get('Categories_de_POI')) if len(nom) >= 3 else None
                if g not in ACTIVITES:
                    continue
                contacts = l.get('Contacts_du_POI') or ''
                if len(EXEMPLES) < 6 and contacts:
                    EXEMPLES.append(contacts[:300])
                mails = sorted({m.lower().rstrip('.') for m in MAIL.findall(contacts)})
                tels = sorted({re.sub(r'[\s.-]', '', t) for t in TEL.findall(contacts)})
                site = premier_lien(contacts) or ''
                if not (mails or tels or site):
                    continue
                cle = (sans_accents(nom), cp)
                if cle in vus:
                    continue
                vus.add(cle)
                lignes.append({
                    'Département': cp[:2], 'Commune': nettoyer(commune, 50), 'Code postal': cp, 'Nom': nom,
                    'Activité': ACTIVITES[g], 'E-mail': ' / '.join(mails[:2]), 'Téléphone': ' / '.join(tels[:2]),
                    'Site': site, 'Adresse': nettoyer((l.get('Adresse_postale') or '').split('#')[0], 100),
                })
    lignes.sort(key=lambda x: (x['Département'], x['Activité'], x['Commune'], x['Nom']))
    with open(sortie, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=';')
        w.writeheader()
        w.writerows(lignes)
    par = {}
    for x in lignes:
        par[x['Activité']] = par.get(x['Activité'], 0) + 1
    import base64, gzip
    print('EXEMPLES_CONTACTS', EXEMPLES[:6])
    print('DEBUT_CSV')
    print(base64.b64encode(gzip.compress(open(sortie, 'rb').read())).decode())
    print('FIN_CSV')
    print(len(lignes), 'entreprises,', sum(1 for x in lignes if x['E-mail']), 'avec e-mail')
    print(sorted(par.items(), key=lambda kv: -kv[1]))


if __name__ == '__main__':
    main()
