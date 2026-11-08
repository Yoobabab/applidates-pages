"""Villes de Belgique, de Suisse, du Luxembourg et de Monaco, pour la recherche de ville de l'appli.

En France, l'appli cherche les communes dans l'annuaire de l'IGN (Géoplateforme) ; il ne couvre pas les pays voisins.
Ce robot publie la liste des villes et villages de ces pays (OpenStreetMap, licence ODbL), lue une fois par l'appli.

Sortie : lieux/v1/villes.json = [[nom, autre nom (français si différent, sinon ""), lat, lon, pays, population], …]

Usage : python3 outils/villes.py dossier_sortie BE:places-be.osm.pbf CH:places-ch.osm.pbf LU:… MC:…
"""

import json
import os
import sys

import osmium

GARDES = {'city', 'town', 'village', 'municipality'}


class Villes(osmium.SimpleHandler):
    def __init__(self, pays):
        super().__init__()
        self.pays = pays
        self.liste = []

    def node(self, n):
        t = n.tags
        if t.get('place') not in GARDES or not t.get('name') or not n.location.valid():
            return
        nom = t.get('name')
        fr = t.get('name:fr') or ''
        if fr == nom:
            fr = ''
        try:
            pop = int(str(t.get('population', '0')).replace(' ', '').replace("'", '').replace('.', '').split(';')[0] or 0)
        except ValueError:
            pop = 0
        # Les villages sans population connue passent après les villes et bourgs.
        if not pop:
            pop = {'city': 50000, 'town': 5000}.get(t.get('place'), 0)
        self.liste.append([nom[:60], fr[:60], round(n.location.lat, 4), round(n.location.lon, 4), self.pays, pop])


def main():
    dossier = sys.argv[1]
    toutes = []
    for arg in sys.argv[2:]:
        pays, fichier = arg.split(':', 1)
        v = Villes(pays)
        v.apply_file(fichier)
        print(pays, len(v.liste))
        toutes += v.liste
    if len(toutes) < 1000:
        sys.exit(f'Trop peu de villes ({len(toutes)}) : rien n’est publié.')
    toutes.sort(key=lambda v: -v[5])
    sortie = os.path.join(dossier, 'lieux', 'v1')
    os.makedirs(sortie, exist_ok=True)
    with open(os.path.join(sortie, 'villes.json'), 'w', encoding='utf-8') as f:
        json.dump(toutes, f, ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    main()
