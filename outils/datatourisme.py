"""Robot de la semaine : lieux d'activités de DATAtourisme (offices de tourisme, licence ouverte Etalab 2.0).

Lit les fichiers « place » et « product » (lieux et offres : domaines qui font déguster, centres équestres,
canoë, accrobranche, musées, sites naturels, visites…), garde ce qui fait une bonne sortie, lui donne un genre
et publie des carrés de 0,1° : lieux/v1/dt/{i}_{j}.json (i = floor(lat × 10)), à côté des lieux OpenStreetMap.

Chaque lieu = {"id", "n" (nom), "g" (genre), "la", "lo", "c" (commune), "a" (adresse), "d" (description), "w" (site)}.
Les genres sont lus par l'appli (src/lib/datatourisme.ts).

Usage : python3 outils/datatourisme.py dossier_sortie place.csv [product.csv …]
"""

import csv
import json
import math
import os
import re
import sys
import unicodedata

CORE = 'https://www.datatourisme.fr/ontology/core#'

# Le nom d'abord (sans accents, minuscules) : c'est lui qui dit le mieux ce qu'on va faire.
PAR_MOTS = [
    ('aerien', r"\b(montgolfiere|parapente|ulm|parachut|bapteme de l.air|helicoptere|deltaplane|vol libre)"),
    ('eaux_vives', r"\b(rafting|canyoning|hydrospeed|eaux vives|nage en eaux)"),
    ('canoe', r"\b(canoe|kayak|paddle|stand up|pedalo)"),
    ('voile', r"\b(voile|catamaran|char a voile|kitesurf|surf|wakeboard|ski nautique|jet ?ski|plongee)"),
    ('bateau', r"\b(croisiere|promenade en bateau|bateau|peniche|gabare|vedette|batobus|coche d.eau)"),
    ('climbing_adventure', r"\b(accrobranche|parc (aventure|acrobatique)|tyrolienne|via ferrata|parcours (aventure|acrobatique))"),
    ('climbing', r"\b(escalade|bloc|grimpe)\b"),
    ('escape', r"\b(escape|room escape|jeu d.evasion|salle d.enigmes)"),
    ('laser_tag', r"\blaser ?(game|tag)\b"),
    ('paintball', r"\bpaint ?ball\b"),
    ('karting', r"\bkarting\b"),
    ('bowling_alley', r"\bbowling\b"),
    ('ice_rink', r"\bpatinoire\b"),
    ('trampoline_park', r"\btrampoline"),
    ('miniature_golf', r"\b(mini[- ]?golf|golf miniature|aventure golf)"),
    ('golf', r"\bgolf\b"),
    ('horse_riding', r"\b(equitation|equestre|balade a cheval|randonnee a cheval|poney|ranch|attelage)"),
    ('velo', r"\b(location de velos?|velo ?rail|velorail|rosalie|trottinette|segway|gyropode|cyclo)"),
    ('theme_park', r"\b(parc d.attractions|parc de loisirs|parc a theme|fete foraine permanente)"),
    ('water_park', r"\b(parc aquatique|aquaparc|toboggans)"),
    ('zoo', r"\b(zoo|parc animalier|reserve africaine|safari|ferme pedagogique|volerie|rapaces)"),
    ('aquarium', r"\baquarium\b"),
    ('planetarium', r"\b(planetarium|observatoire)"),
    ('bains', r"\b(spa|hammam|thermes|thalasso|bains|sauna|bien[- ]etre|balneo)"),
    ('atelier', r"\b(atelier|cours de cuisine|poterie|ceramique|souffleur de verre|initiation a)"),
    ('winery', r"\b(degustation|caveau|cave|domaine|vignoble|vigneron|chateau .{0,30}(vin|cru)|oenolog|brasserie|distillerie|cidrerie|champagne)"),
    ('museum', r"\b(musee|museum|ecomusee)"),
    ('visite', r"\b(visite guidee|visite insolite|chateau|abbaye|citadelle|fort\b|grotte|gouffre|aven\b|souterrain)"),
]

# Par catégorie DATAtourisme, quand le nom n'a rien dit.
PAR_CATEGORIE = [
    ('winery', {'TastingProvider', 'Tasting'}),
    ('horse_riding', {'EquestrianCenter'}),
    ('museum', {'Museum'}),
    ('parc', {'ParkAndGarden'}),
    ('nature', {'NaturalHeritage'}),
    ('visite', {'Visit', 'RemarkableBuilding', 'Castle', 'CityHeritage'}),
]

# Rien à faire pour un date : hébergements, commerces, lieux de culte, services, stages et cours longs.
EXCLURE = {
    'Accommodation', 'AccommodationProduct', 'HotelTrade', 'CampingAndCaravanning', 'CamperVanArea',
    'TouristInformationCenter', 'LocalTouristOffice', 'Library', 'ReligiousSite', 'Church', 'Transport',
    'BusinessPlace', 'ConventionCentre', 'MultiPurposeRoomOrCommunityRoom', 'Traineeship', 'ChildrensEvent',
    'FoodEstablishment', 'PicnicArea', 'Tour', 'WalkingTour',
}
# Gardés malgré EXCLURE quand c'est un vrai prestataire (un domaine qui fait aussi gîte, par exemple).
SAUVER = {'TastingProvider', 'ActivityProvider', 'LeisureSportActivityProvider', 'EquestrianCenter', 'Museum'}

ENFANTS = r"\b(jeune public|enfants?|tout[- ]petits|bebes?|p.tits|kids|anniversaire enfant)\b"


def sans_accents(texte):
    return unicodedata.normalize('NFD', texte or '').encode('ascii', 'ignore').decode().lower()


def nettoyer(texte, maxi):
    texte = re.sub(r'\s+', ' ', texte or '').strip()
    if len(texte) <= maxi:
        return texte
    coupe = texte[: maxi - 1]
    return (coupe.rsplit(' ', 1)[0] if ' ' in coupe else coupe).rstrip(' ,;:.') + '…'


def premier_lien(contacts):
    for m in re.finditer(r'https?://[^\s<>#|]+', contacts or ''):
        lien = m.group(0).rstrip('.,;)')
        # Les pages Facebook ou des réseaux sociaux n'aident pas à réserver : on garde un vrai site si possible.
        if not re.search(r'facebook|instagram|twitter|youtube|tripadvisor', lien):
            return lien[:200]
    return None


def genre(nom, categories):
    noms = {c.split('#')[-1] for c in (categories or '').split('|') if c.startswith(CORE)}
    if (noms & EXCLURE) and not (noms & SAUVER):
        return None
    texte = sans_accents(nom)
    if re.search(ENFANTS, texte):
        return None
    for g, motif in PAR_MOTS:
        if re.search(motif, texte):
            # « Domaine » ou « château » seuls ne suffisent pas : il faut que ce soit un lieu qui fait déguster.
            if g == 'winery' and not (noms & {'TastingProvider', 'Tasting', 'Producer', 'LocalProductsShop'}) and not re.search(r'degustation|caveau|cave|vigneron|vignoble', texte):
                continue
            if g == 'visite' and not (noms & {'CulturalSite', 'Visit', 'RemarkableBuilding', 'Castle', 'NaturalHeritage', 'CityHeritage'}):
                continue
            return g
    for g, liste in PAR_CATEGORIE:
        if noms & liste:
            return g
    return None


def lire(chemin, sortie, vus, compte):
    csv.field_size_limit(10**9)
    with open(chemin, encoding='utf-8', newline='') as f:
        for ligne in csv.DictReader(f):
            try:
                lat = float(ligne['Latitude'])
                lon = float(ligne['Longitude'])
            except (KeyError, ValueError, TypeError):
                continue
            if not (41 <= lat <= 52 and -6 <= lon <= 10):
                continue  # France métropolitaine (les carrés de l'appli ne couvrent pas l'outre-mer pour l'instant)
            nom = nettoyer(ligne.get('Nom_du_POI'), 90)
            if len(nom) < 3:
                continue
            g = genre(nom, ligne.get('Categories_de_POI'))
            if not g:
                continue
            # Même lieu publié par deux offices de tourisme, ou présent dans les deux fichiers : gardé une fois.
            cle = (sans_accents(nom), round(lat, 3), round(lon, 3))
            if cle in vus:
                continue
            vus.add(cle)
            _, _, commune = (ligne.get('Code_postal_et_commune') or '').partition('#')
            lieu = {
                'id': (ligne.get('URI_ID_du_POI') or '').rsplit('/', 1)[-1][:40] or f'{lat:.4f}_{lon:.4f}',
                'n': nom,
                'g': g,
                'la': round(lat, 5),
                'lo': round(lon, 5),
                'c': nettoyer(commune, 50),
            }
            adresse = nettoyer((ligne.get('Adresse_postale') or '').split('#')[0], 100)
            if adresse:
                lieu['a'] = adresse
            description = nettoyer(ligne.get('Description'), 180)
            if description:
                lieu['d'] = description
            lien = premier_lien(ligne.get('Contacts_du_POI'))
            if lien:
                lieu['w'] = lien
            sortie.setdefault(f'{math.floor(lat * 10)}_{math.floor(lon * 10)}', []).append(lieu)
            compte[g] = compte.get(g, 0) + 1


def main():
    dossier, fichiers = sys.argv[1], sys.argv[2:]
    carres, vus, compte = {}, set(), {}
    for chemin in fichiers:
        lire(chemin, carres, vus, compte)
    total = sum(compte.values())
    if total < 5000:
        # Garde-fou : un fichier source vide ou cassé ne publie rien (l'appli garde alors OpenStreetMap seul).
        sys.exit(f'Trop peu de lieux DATAtourisme ({total}) : rien n’est publié.')
    sortie = os.path.join(dossier, 'lieux', 'v1', 'dt')
    os.makedirs(sortie, exist_ok=True)
    for cle, liste in carres.items():
        with open(os.path.join(sortie, f'{cle}.json'), 'w', encoding='utf-8') as f:
            json.dump(liste, f, ensure_ascii=False, separators=(',', ':'))
    index = {'source': 'DATAtourisme (licence ouverte Etalab 2.0)', 'total': total, 'genres': dict(sorted(compte.items())), 'carres': len(carres)}
    with open(os.path.join(sortie, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print(json.dumps(index, ensure_ascii=False))


if __name__ == '__main__':
    main()
