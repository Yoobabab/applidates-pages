"""Robot de nuit : événements à venir en France, tirés du fichier quotidien DATAtourisme (licence ouverte Etalab 2.0).

Garde les événements des 60 prochains jours, leur donne un genre (fête, concert, spectacle, marché, auto/moto,
expo, dégustation), et publie des tuiles de 1° × 1° : evenements/v1/{lat}_{lon}.json, plus index.json.
Les événements « mis en avant » (payés par l'organisateur) sont lus dans outils/en-avant.json.

Usage : python3 outils/evenements.py fichier.csv dossier_sortie [AAAA-MM-JJ]
"""

import csv
import datetime as dt
import json
import math
import os
import re
import sys
import unicodedata

HORIZON_JOURS = 60
# Au-delà, c'est une offre permanente (visite, atelier toute l'année), pas un événement.
DUREE_MAX_JOURS = 21

CORE = 'https://www.datatourisme.fr/ontology/core#'

# Genre par catégorie DATAtourisme (ordre = priorité).
PAR_CATEGORIE = [
    ('fete', {'TraditionalCelebration', 'LocalAnimation', 'Carnival', 'SocialEvent'}),
    ('concert', {'Concert', 'Festival'}),
    ('spectacle', {'ShowEvent', 'TheaterEvent', 'ScreeningEvent', 'DanceEvent', 'CircusEvent', 'Recital'}),
    ('marche', {'Market', 'SaleEvent', 'GarageSale', 'FairOrShow'}),
    ('expo', {'Exhibition', 'VisualArtsEvent'}),
    ('degustation', {'Tasting'}),
]

# Mots-clés du nom (sans accents, minuscules) : priment sur les catégories.
PAR_MOTS = [
    ('auto', r"\b(voitures?|autos?|automobiles?|moto(s|rs)?|tuning|car ?meet|rassemblement (de |d.)?(vehicules|voitures|motos|vespa|2cv|youngtimers?|americaines?)|retromobile|salon de l.auto|rallye auto|vehicules anciens|belles mecaniques|us cars?)\b"),
    ('fete', r"\b(fete foraine|foire|feria|bodega|abrivado|bandido|fete votive|fete du village|carnaval|corso|fete locale|fete patronale|fete de la (biere|musique)|festivites|guinguette|bal\b)"),
    ('concert', r"\b(concerts?|festival|dj set|live music|musique live|orchestre)\b"),
    ('marche', r"\b(brocantes?|vide[- ]greniers?|marche de noel|marche nocturne|puces|bourse aux)\b"),
]

# Sans intérêt pour une sortie (stages, conférences, ateliers pour enfants…), sauf si le nom dit clairement le contraire.
# Les « SportsEvent » sont écartés : la catégorie sert surtout aux randonnées et visites de domaines.
EXCLURE = {'Traineeship', 'Conference', 'BusinessEvent', 'Practice', 'ChildrensEvent', 'Rambling', 'OpenDay'}


def sans_accents(texte):
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode().lower()


def lire_periodes(texte, debut, fin):
    """« 2026-10-17<->2026-10-18|2026-10-24<->2026-10-24 » → périodes coupées à la fenêtre [debut, fin]."""
    periodes = []
    for morceau in (texte or '').split('|'):
        m = re.match(r'\s*(\d{4}-\d{2}-\d{2})\S*\s*<->\s*(\d{4}-\d{2}-\d{2})', morceau)
        if not m:
            continue
        a = dt.date.fromisoformat(m.group(1))
        b = dt.date.fromisoformat(m.group(2))
        if b < a or (b - a).days > DUREE_MAX_JOURS or b < debut or a > fin:
            continue
        periodes.append([max(a, debut).isoformat(), min(b, fin).isoformat()])
    return periodes


def genre(nom, categories):
    texte = sans_accents(nom)
    for g, motif in PAR_MOTS:
        if re.search(motif, texte):
            return g
    noms = {c.split('#')[-1] for c in categories.split('|') if c.startswith(CORE)}
    if noms & EXCLURE:
        return None
    for g, liste in PAR_CATEGORIE:
        if noms & liste:
            return g
    return None


def premier_lien(contacts):
    for m in re.finditer(r'https?://[^\s<>#|]+', contacts or ''):
        return m.group(0)
    return None


def nettoyer(texte, maxi):
    texte = re.sub(r'\s+', ' ', texte or '').strip()
    return texte if len(texte) <= maxi else texte[: maxi - 1].rstrip() + '…'


def tuile(lat, lon):
    return f'{math.floor(lat)}_{math.floor(lon)}'


def construire(chemin_csv, aujourdhui):
    debut = aujourdhui
    fin = aujourdhui + dt.timedelta(days=HORIZON_JOURS)
    csv.field_size_limit(10**9)
    tuiles = {}
    vus = set()
    compte = {}
    with open(chemin_csv, encoding='utf-8', newline='') as f:
        for ligne in csv.DictReader(f):
            try:
                lat = float(ligne['Latitude'])
                lon = float(ligne['Longitude'])
            except (KeyError, ValueError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            nom = nettoyer(ligne.get('Nom_du_POI'), 100)
            if not nom:
                continue
            g = genre(nom, ligne.get('Categories_de_POI', ''))
            if not g:
                continue
            periodes = lire_periodes(ligne.get('Periodes_regroupees'), debut, fin)
            if not periodes:
                continue
            ident = (ligne.get('URI_ID_du_POI') or '').rsplit('/', 1)[-1][:40] or f'{lat:.4f},{lon:.4f},{nom}'
            # Même événement publié par deux offices de tourisme : on le garde une fois.
            cle = (sans_accents(nom), round(lat, 3), round(lon, 3), periodes[0][0])
            if cle in vus:
                continue
            vus.add(cle)
            cp, _, commune = (ligne.get('Code_postal_et_commune') or '').partition('#')
            evenement = {
                'id': ident,
                'nom': nom,
                'genre': g,
                'lat': round(lat, 5),
                'lon': round(lon, 5),
                'commune': nettoyer(commune, 60),
                'adresse': nettoyer(ligne.get('Adresse_postale'), 120),
                'periodes': periodes,
                'description': nettoyer(ligne.get('Description'), 240),
            }
            lien = premier_lien(ligne.get('Contacts_du_POI'))
            if lien:
                evenement['lien'] = lien
            tuiles.setdefault(tuile(lat, lon), []).append(evenement)
            compte[g] = compte.get(g, 0) + 1
    return tuiles, compte


def ajouter_en_avant(tuiles, chemin, aujourdhui):
    """Événements payés par leur organisateur : marqués « sponsorise » (affichés « Mis en avant »)."""
    if not os.path.exists(chemin):
        return 0
    n = 0
    for e in json.load(open(chemin, encoding='utf-8')):
        if e.get('jusquau', '9999-12-31') < aujourdhui.isoformat():
            continue
        e = {k: v for k, v in e.items() if k != 'jusquau'}
        e['sponsorise'] = True
        tuiles.setdefault(tuile(e['lat'], e['lon']), []).append(e)
        n += 1
    return n


def publier(tuiles, compte, dossier, aujourdhui, en_avant):
    sortie = os.path.join(dossier, 'evenements', 'v1')
    os.makedirs(sortie, exist_ok=True)
    for cle, liste in tuiles.items():
        liste.sort(key=lambda e: (not e.get('sponsorise'), e['periodes'][0][0]))
        with open(os.path.join(sortie, f'{cle}.json'), 'w', encoding='utf-8') as f:
            json.dump(liste, f, ensure_ascii=False, separators=(',', ':'))
    index = {
        'maj': aujourdhui.isoformat(),
        'source': 'DATAtourisme (licence ouverte Etalab 2.0)',
        'total': sum(len(l) for l in tuiles.values()),
        'en_avant': en_avant,
        'genres': compte,
        'tuiles': sorted(tuiles),
    }
    with open(os.path.join(sortie, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    return index


if __name__ == '__main__':
    chemin, dossier = sys.argv[1], sys.argv[2]
    jour = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else dt.date.today()
    t, c = construire(chemin, jour)
    n = ajouter_en_avant(t, os.path.join(os.path.dirname(__file__), 'en-avant.json'), jour)
    i = publier(t, c, dossier, jour, n)
    if i['total'] < 1000:
        # Garde-fou : un fichier source vide ou cassé ne doit pas effacer les événements publiés.
        sys.exit(f"Trop peu d'événements ({i['total']}) : rien n'est publié.")
    print(json.dumps({k: v for k, v in i.items() if k != 'tuiles'}, ensure_ascii=False, indent=1))
