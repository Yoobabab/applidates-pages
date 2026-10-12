# AppliDates — pages publiques

Pages web ouvertes par les personnes qui reçoivent un lien depuis l'appli AppliDates (sans rien installer).

- `surprise/?id=…` : un date surprise qui se dévoile étape par étape.
- `vote/?id=…` : le vote du groupe entre 3 programmes.

La source de ces pages est dans le dépôt privé de l'appli (`pages/`). Ne pas modifier ici directement.

## Événements (robot de nuit)

`outils/evenements.py`, lancé chaque nuit par `.github/workflows/evenements.yml` : lit le fichier quotidien des
événements DATAtourisme (licence ouverte Etalab 2.0), garde les 60 prochains jours, classe chaque événement
(fête/féria, concert/festival, spectacle, marché/brocante, auto/moto, expo, dégustation) et publie des tuiles
de 1° sur la branche `donnees` (`evenements/v1/{lat}_{lon}.json`, `index.json`).

Événements **mis en avant** (payés par l'organisateur) : à ajouter dans `outils/en-avant.json`, ils sont affichés
avec la mention « Mis en avant » dans l'appli. Exemple :

```json
[
  {
    "id": "pro-feria-nimes-2026",
    "nom": "Bodega du Club taurin",
    "genre": "fete",
    "lat": 43.8367, "lon": 4.3601,
    "commune": "Nîmes", "adresse": "Place des Arènes",
    "periodes": [["2026-10-16", "2026-10-18"]],
    "description": "Bodega, DJ et tapas jusqu'à 2 h.",
    "lien": "https://exemple.fr",
    "jusquau": "2026-10-18"
  }
]
```

## Lieux de France (robot de la semaine)

`outils/lieux.py`, lancé chaque lundi par `.github/workflows/lieux.yml` : télécharge l'extrait France d'OpenStreetMap
(Geofabrik), garde les restos, bars, cafés, boîtes, cinémas, jeux, sensations, salles, musées, parcs, points de vue,
plages et stades, et compte combien il y en a par carrés de 0,05° (≈ 5 km). Publié sur la branche `lieux`
(`lieux/v1/comptes/{lat}_{lon}.json`, `index.json`). Données © contributeurs OpenStreetMap, licence ODbL.

## Matchs (robot de nuit)

`outils/matchs.py`, lancé avec les événements : matchs de foot pas encore joués dans un stade français (et Monaco)
dans les 60 prochains jours (Ligue 1, Ligue 2, coupes d'Europe ; source fixturedownload.com), avec heure de Paris
et position du stade → `matchs/v1/matchs.json` sur la branche `donnees`. Nouveau stade : l'ajouter dans `STADES`.
