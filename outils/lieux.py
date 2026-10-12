"""Robot de la semaine : combien de restos, bars, cinémas, parcs… partout en France, par carrés de 0,05° (≈ 5 km).

Source : extrait France d'OpenStreetMap (Geofabrik), déjà filtré par osmium sur les étiquettes utiles.
L'appli additionne les carrés dont le centre est dans le rayon choisi : plus besoin d'interroger les serveurs
publics Overpass, souvent saturés, pour l'accueil.

Sorties :
- lieux/v1/comptes/{lat}_{lon}.json (tuile de 1°) = {"i_j": [n par rubrique]} et lieux/v1/index.json (accueil) ;
- les lieux eux-mêmes, pour composer les programmes, par carrés de 0,1° (≈ 10 km) :
  lieux/v1/t/{i}_{j}.json (restos, sur le pouce, bars, cafés) et lieux/v1/s/{i}_{j}.json (tout le reste),
  avec i = floor(lat × 10), j = floor(lon × 10). Chaque lieu = [id, lat, lon, {étiquettes abrégées}].

Usage : python3 outils/lieux.py france-filtre.osm.pbf dossier_sortie
"""

import json
import math
import os
import sys

import osmium

PAS = 0.05  # taille d'un carré, en degrés
PAR_DEGRE = round(1 / PAS)

# Même ordre et mêmes identifiants que RUBRIQUES dans l'appli (src/lib/inventaire-outils.ts).
RUBRIQUES = ['restos', 'pouce', 'bars', 'cafes', 'boites', 'cinemas', 'jeux', 'sensations', 'scenes', 'musees', 'parcs', 'vues', 'plages', 'stades']
RANG = {r: i for i, r in enumerate(RUBRIQUES)}

# Rubriques « à table » (fichiers t/, lus dans un petit rayon) ; les autres vont dans s/.
TABLE = {'restos', 'pouce', 'bars', 'cafes'}

# Étiquettes gardées pour l'appli, sous un nom court (longueur maximale).
ETIQUETTES = {
    'name': ('n', 80), 'amenity': ('am', 30), 'leisure': ('le', 30), 'tourism': ('to', 30), 'sport': ('sp', 30),
    'natural': ('na', 30), 'cuisine': ('cu', 40), 'opening_hours': ('oh', 160),
    'addr:housenumber': ('hn', 12), 'addr:street': ('st', 80), 'addr:city': ('ci', 60),
}


def abreger(tags):
    return {court: tags.get(long)[:maxi] for long, (court, maxi) in ETIQUETTES.items() if tags.get(long)}


def rubrique(t):
    """Rubrique d'un objet OSM d'après ses étiquettes (None si sans intérêt)."""
    nom = t.get('name')
    amenity, leisure, tourism, sport = t.get('amenity'), t.get('leisure'), t.get('tourism'), t.get('sport')
    if tourism == 'viewpoint':
        return 'vues'
    if not nom:
        return None
    if amenity == 'restaurant':
        return 'restos'
    if amenity == 'fast_food':
        return 'pouce'
    if amenity in ('bar', 'pub'):
        return 'bars'
    if amenity == 'cafe':
        return 'cafes'
    if amenity == 'nightclub':
        return 'boites'
    if amenity == 'cinema':
        return 'cinemas'
    if amenity in ('theatre', 'arts_centre', 'music_venue'):
        return 'scenes'
    if leisure in ('bowling_alley', 'escape_game', 'amusement_arcade', 'miniature_golf') or sport == 'laser_tag':
        return 'jeux'
    if sport in ('karting', 'paintball') or leisure in ('water_park', 'trampoline_park'):
        return 'sensations'
    if tourism in ('museum', 'gallery'):
        return 'musees'
    if leisure in ('park', 'garden') and t.get('access') != 'private':
        return 'parcs'
    if t.get('natural') == 'beach':
        return 'plages'
    if leisure == 'stadium':
        return 'stades'
    return None


class Compteur(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.tuiles = {}
        self.total = [0] * len(RUBRIQUES)
        self.lieux = {}

    def garder(self, r, ident, lat, lon, tags):
        if r is None:
            return
        famille = 't' if r in TABLE else 's'
        cle = f'{famille}/{math.floor(lat * 10)}_{math.floor(lon * 10)}'
        self.lieux.setdefault(cle, []).append([ident, round(lat, 5), round(lon, 5), abreger(tags)])

    def ajouter(self, r, lat, lon):
        if r is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return
        i, j = math.floor(lat * PAR_DEGRE), math.floor(lon * PAR_DEGRE)
        cle_tuile = f'{math.floor(lat)}_{math.floor(lon)}'
        cle_carre = f'{i - math.floor(lat) * PAR_DEGRE}_{j - math.floor(lon) * PAR_DEGRE}'
        carres = self.tuiles.setdefault(cle_tuile, {})
        compte = carres.setdefault(cle_carre, [0] * len(RUBRIQUES))
        compte[RANG[r]] += 1
        self.total[RANG[r]] += 1

    def node(self, n):
        if n.location.valid():
            r = rubrique(n.tags)
            self.ajouter(r, n.location.lat, n.location.lon)
            self.garder(r, f'n{n.id}', n.location.lat, n.location.lon, n.tags)

    def way(self, w):
        r = rubrique(w.tags)
        if r is None:
            return
        # Point représentatif : moyenne des nœuds (suffisant pour savoir dans quel carré il tombe).
        pts = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]
        if pts:
            lat, lon = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            self.ajouter(r, lat, lon)
            self.garder(r, f'w{w.id}', lat, lon, w.tags)


def main():
    source, dossier = sys.argv[1], sys.argv[2]
    c = Compteur()
    c.apply_file(source, locations=True, idx='flex_mem')
    total = sum(c.total)
    if total < 100000:
        # Garde-fou : un fichier source tronqué ne doit pas remplacer les chiffres publiés.
        sys.exit(f'Trop peu de lieux ({total}) : rien n’est publié.')
    sortie = os.path.join(dossier, 'lieux', 'v1')
    os.makedirs(os.path.join(sortie, 'comptes'), exist_ok=True)
    for cle, carres in c.tuiles.items():
        # Carrés vides de 0 retirés : on n'écrit que les nombres utiles.
        with open(os.path.join(sortie, 'comptes', f'{cle}.json'), 'w', encoding='utf-8') as f:
            json.dump(carres, f, separators=(',', ':'))
    for cle, liste in c.lieux.items():
        os.makedirs(os.path.join(sortie, os.path.dirname(cle)), exist_ok=True)
        with open(os.path.join(sortie, f'{cle}.json'), 'w', encoding='utf-8') as f:
            json.dump(liste, f, ensure_ascii=False, separators=(',', ':'))
    index = {
        'source': 'OpenStreetMap (contributeurs, licence ODbL), extrait Geofabrik',
        'pas': PAS,
        'rubriques': RUBRIQUES,
        'totaux': dict(zip(RUBRIQUES, c.total)),
        'tuiles': sorted(c.tuiles),
        'carres_lieux': len(c.lieux),
    }
    with open(os.path.join(sortie, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print(json.dumps(index['totaux'], ensure_ascii=False))


if __name__ == '__main__':
    main()
