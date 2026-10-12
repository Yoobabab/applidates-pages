"""Calendrier des matchs de foot joués en France (et à Monaco) dans les 60 prochains jours.

Source : fixturedownload.com (Ligue 1, Ligue 2, Ligue des champions, Ligue Europa, Ligue Conférence).
On ne garde que les matchs pas encore joués dans un stade connu (table ci-dessous, avec sa position).
Sortie : matchs/v1/matchs.json. Si les calendriers ne répondent pas, on reprend le fichier publié la veille.

Usage : python3 outils/matchs.py dossier_sortie [AAAA-MM-JJ]
"""

import datetime as dt
import json
import os
import re
import sys
import unicodedata
import urllib.request
from zoneinfo import ZoneInfo

COMPETITIONS = {
    'ligue-1-2026': 'Ligue 1',
    'ligue-2-2026': 'Ligue 2',
    'champions-league-2026': 'Ligue des champions',
    'europa-league-2026': 'Ligue Europa',
    'conference-league-2026': 'Ligue Conférence',
}
SOURCE = 'https://fixturedownload.com/feed/json/{}'
VEILLE = 'https://raw.githubusercontent.com/Yoobabab/applidates-pages/donnees/matchs/v1/matchs.json'
AGENT = 'AppliDates/0.9 (contact@shivr.fr)'
HORIZON_JOURS = 60
PARIS = ZoneInfo('Europe/Paris')

# Stades (nom tel qu'écrit dans les calendriers → ville, latitude, longitude).
STADES = {
    'Allianz Riviera': ('Nice', 43.7052, 7.1926),
    'Parc Olympique Lyonnais': ('Décines-Charpieu', 45.7653, 4.9822),
    'OL Stadium': ('Décines-Charpieu', 45.7653, 4.9822),
    'Parc des Princes': ('Paris', 48.8414, 2.2530),
    'Roazhon Park': ('Rennes', 48.1076, -1.7128),
    'Stade Bollaert-Delelis': ('Lens', 50.4328, 2.8150),
    'Stade Charléty': ('Paris', 48.8187, 2.3462),
    'Stade Jean-Bouin': ('Paris', 48.8433, 2.2525),
    'Stade Francis-Le Blé': ('Brest', 48.4029, -4.4617),
    'Stade Louis II': ('Monaco', 43.7276, 7.4155),
    'Stade Marie-Marvingt': ('Le Mans', 47.9567, 0.2242),
    'Stade Océane': ('Le Havre', 49.4988, 0.1697),
    'Stade Pierre-Mauroy': ('Villeneuve-d’Ascq', 50.6119, 3.1305),
    'Stade Raymond Kopa': ('Angers', 47.4604, -0.5308),
    'Stade Vélodrome': ('Marseille', 43.2698, 5.3959),
    "Stade de l'Abbé-Deschamps": ('Auxerre', 47.7867, 3.5886),
    "Stade de l'Aube": ('Troyes', 48.3075, 4.0985),
    'Stade de la Meinau': ('Strasbourg', 48.5600, 7.7550),
    'Stade du Moustoir': ('Lorient', 47.7488, -3.3694),
    'Stadium de Toulouse': ('Toulouse', 43.5833, 1.4342),
    'Nouste Camp': ('Pau', 43.3155, -0.3195),
    'Parc des Sports': ('Annecy', 45.9089, 6.1265),
    'Stade Auguste-Bonal': ('Montbéliard', 47.5124, 6.8114),
    'Stade Auguste-Delaune': ('Reims', 49.2467, 4.0250),
    'Stade Bauer': ('Saint-Ouen', 48.9065, 2.3428),
    'Stade Francis Le Basser': ('Laval', 48.0598, -0.7646),
    'Stade Gabriel-Montpied': ('Clermont-Ferrand', 45.8159, 3.1214),
    'Stade Gaston-Gérard': ('Dijon', 47.3245, 5.0684),
    'Stade Geoffroy-Guichard': ('Saint-Étienne', 45.4608, 4.3903),
    'Stade Marcel-Picot': ('Tomblaine', 48.6953, 6.2108),
    'Stade Marcel-Tribut': ('Dunkerque', 51.0420, 2.3600),
    'Stade Paul-Lignon': ('Rodez', 44.3500, 2.5650),
    'Stade Saint-Symphorien': ('Metz', 49.1097, 6.1594),
    'Stade de la Beaujoire': ('Nantes', 47.2560, -1.5254),
    'Stade de la Libération': ('Boulogne-sur-Mer', 50.7272, 1.6213),
    'Stade de la Mosson': ('Montpellier', 43.6222, 3.8121),
    'Stade des Alpes': ('Grenoble', 45.1874, 5.7398),
    'Stade municipal de Roudourou': ('Guingamp', 48.5660, -3.1645),
}


def cle(nom):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFD', nom or '').encode('ascii', 'ignore').decode().lower())


PAR_CLE = {cle(n): (n, *v) for n, v in STADES.items()}


def lire(url):
    req = urllib.request.Request(url, headers={'User-Agent': AGENT})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode('utf-8'))


def construire(aujourdhui):
    fin = aujourdhui + dt.timedelta(days=HORIZON_JOURS)
    matchs, reussies = [], 0
    for code, nom in COMPETITIONS.items():
        try:
            donnees = lire(SOURCE.format(code))
        except Exception as e:  # noqa: BLE001 — une compétition indisponible ne bloque pas les autres
            print(f'{nom} : indisponible ({e})', file=sys.stderr)
            continue
        reussies += 1
        for m in donnees:
            stade = PAR_CLE.get(cle(m.get('Location')))
            if not stade or m.get('HomeTeamScore') is not None:
                continue
            try:
                debut = dt.datetime.strptime(m['DateUtc'], '%Y-%m-%d %H:%M:%SZ').replace(tzinfo=dt.timezone.utc).astimezone(PARIS)
            except (KeyError, ValueError):
                continue
            if not (aujourdhui <= debut.date() <= fin):
                continue
            nom_stade, ville, lat, lon = stade
            matchs.append({
                'id': f"{code}-{m.get('MatchNumber')}",
                'competition': nom,
                'debut': debut.strftime('%Y-%m-%dT%H:%M'),
                'domicile': m.get('HomeTeam') or '',
                'exterieur': m.get('AwayTeam') or '',
                'stade': nom_stade,
                'ville': ville,
                'lat': lat,
                'lon': lon,
            })
    matchs.sort(key=lambda m: m['debut'])
    return matchs, reussies


def main():
    dossier = sys.argv[1]
    jour = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.datetime.now(PARIS).date()
    matchs, reussies = construire(jour)
    if reussies == 0:
        # Calendriers injoignables : on garde la version de la veille plutôt que de tout effacer.
        try:
            matchs = [m for m in lire(VEILLE) if m['debut'][:10] >= jour.isoformat()]
            print('Calendriers injoignables : version de la veille reprise.', file=sys.stderr)
        except Exception:  # noqa: BLE001
            matchs = []
    sortie = os.path.join(dossier, 'matchs', 'v1')
    os.makedirs(sortie, exist_ok=True)
    with open(os.path.join(sortie, 'matchs.json'), 'w', encoding='utf-8') as f:
        json.dump(matchs, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{len(matchs)} matchs à venir ({reussies}/{len(COMPETITIONS)} calendriers lus).')


if __name__ == '__main__':
    main()
