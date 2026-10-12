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
