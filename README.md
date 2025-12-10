# Projet NoSQL - Système de Livraison en Temps Réel

Projet de gestion d'un système de livraison utilisant **Redis** pour le temps réel et **MongoDB** pour l'historique et les analyses.

## Équipe

- **Ilies IDIR**
- **Haci YILMAZER**
- **Steven CARLOT**
- **Karima MAHI**

## Technologies

- **Redis Cloud** - Gestion temps réel (livreurs, commandes, géolocalisation)
- **MongoDB Atlas** - Historique et analyses des livraisons
- **Python 3.13** - Langage de développement
- **Streamlit** - Dashboard interactif
- **Folium** - Visualisation cartographique

---

## Architecture du Projet
```
Projet-No-Sql/
├── config/
│   ├── redis_config.py          # Configuration Redis Cloud
│   └── mongodb_config.py        # Configuration MongoDB Atlas
├── redis/
│   ├── partie1_temps_reel.py    # PARTIE 1 : État temps réel (6 travaux)
│   ├── partie3_avancees.py      # PARTIE 3 : Structures avancées (2 travaux)
│   ├── partie4_geospatial.py    # PARTIE 4 : Geo-spatial (4 travaux)
│   ├── partie4_bonus_gui.py     # BONUS : Dashboard interactif Streamlit
│   └── test_connection.py       # Test connexion Redis
├── mongodb/
│   ├── partie2_historique.py    # PARTIE 2 : Historique et analyses (6 travaux)
│   └── utils.py                 # Utilitaires MongoDB
├── docs/
│   └── rapport.md               # Rapport détaillé du projet
├── requirements.txt             # Dépendances Python
└── README.md                    # Ce fichier
```

---

## Installation

### 1. Cloner le repository
```bash
git clone https://github.com/S13v3n-2/Projet-No-Sql.git
cd Projet-No-Sql
```

### 2. Créer un environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration

Créer un fichier `.env` à la racine avec vos credentials (fichier déjà présent, à ne pas commit) :
```env
# Redis Cloud
REDIS_HOST=votre-host.cloud.redislabs.com
REDIS_PORT=18412
REDIS_PASSWORD=votre_password

# MongoDB Atlas (déjà configuré dans mongodb_config.py)
```

---

## Utilisation

### Tester Redis - Partie Temps Réel

#### Partie 1 : État temps réel (Livreurs et Commandes)
```bash
python redis/partie1_temps_reel.py
```

**Fonctionnalités :**
- Initialisation de 6 livreurs avec ratings
- Création de 6 commandes
- Affectation atomique d'une commande à un livreur (transaction)
- Simulation de livraison complétée
- Dashboard temps réel avec statistiques

#### Partie 3 : Structures avancées
```bash
python redis/partie3_avancees.py
```

**Fonctionnalités :**
- Livreurs multi-régions (Paris, Banlieue, Province)
- Cache avec expiration automatique (TTL 30s)
- Recherche de livreurs par région

#### Partie 4 : Geo-spatial
```bash
python redis/partie4_geospatial.py
```

**Fonctionnalités :**
- Stockage positions GPS des livreurs et lieux
- Recherche de livreurs dans un rayon (2 km, 3 km)
- Affectation optimale (3 stratégies : proximité, rating, équilibre)
- Monitoring des zones de service

#### BONUS : Dashboard Interactif
```bash
streamlit run redis/partie4_bonus_gui.py
```

**Fonctionnalités :**
- Carte interactive avec positions GPS en temps réel
- État temps réel des livreurs et alertes
- Centre de notifications pour livreurs hors zone
- Détails de la flotte avec distances
- Simulation et réinitialisation

---

### Tester MongoDB - Partie Historique

#### Partie 2 : Historique et analyses
```bash
python mongodb/partie2_historique.py
```

**Fonctionnalités :**
- Import de 6 livraisons complétées
- Historique par livreur avec statistiques
- Performance par région (nb livraisons, revenu, durée, rating)
- Top 2 livreurs par revenu
- Indexation stratégique (driver_id, region+delivery_time)
- Logique de synchronisation Redis → MongoDB

---

## Concepts Redis Utilisés

### Structures de données

| Structure | Usage | Exemple |
|-----------|-------|---------|
| **Hash** | Infos livreurs/commandes | `livreur:d1` → {nom, rating, ...} |
| **Set** | Groupement par statut | `commandes:en_attente` → {c1, c2, c3} |
| **Sorted Set** | Classement par rating | `livreurs:ratings` → d3:4.9, d1:4.8... |
| **Geo** | Positions GPS | `drivers_locations` → coordonnées |

### Commandes clés

- **HSET/HGET** : Stocker/récupérer données livreurs
- **ZADD/ZREVRANGE** : Ranking des livreurs par rating
- **SADD/SMEMBERS** : Gestion des statuts de commandes
- **GEOADD/GEORADIUS** : Localisation et recherche par proximité
- **PIPELINE/EXECUTE** : Transactions atomiques
- **EXPIRE** : Cache avec TTL

---

## Concepts MongoDB Utilisés

### Opérations

| Opération | Usage | Exemple |
|-----------|-------|---------|
| **insert_many** | Import historique | 6 livraisons initiales |
| **find** | Requêtes simples | Livraisons d'un livreur |
| **aggregate** | Analyses complexes | Performance par région |
| **create_index** | Optimisation | Index sur driver_id |

### Pipeline d'agrégation
```javascript
// Exemple : Performance par région
[
  { $group: {
      _id: "$region",
      nb_livraisons: { $sum: 1 },
      revenu_total: { $sum: "$amount" },
      rating_moyen: { $avg: "$rating" }
  }},
  { $sort: { revenu_total: -1 }}
]
```

---

## Choix Techniques

### Redis pour le temps réel

**Avantages :**
- Latence ultra-faible (< 1ms)
- Structures de données riches (Sorted Sets, Geo)
- Transactions atomiques (MULTI/EXEC)
- Cache avec expiration automatique (TTL)

**Cas d'usage :**
- Positions GPS des livreurs
- Statuts des commandes en cours
- Ranking en temps réel
- Cache des requêtes fréquentes

### MongoDB pour l'historique

**Avantages :**
- Persistance des données
- Agrégations puissantes
- Indexation flexible
- Requêtes complexes

**Cas d'usage :**
- Historique complet des livraisons
- Analyses de performance
- Statistiques par livreur/région
- Calculs sur grandes périodes

---

## Tests et Validation

### Vérification Redis
```bash
# Test connexion
python redis/test_connection.py

# Vérifier dans Redis CLI
redis-cli -h <host> -p <port> -a <password>
> KEYS *
> HGETALL livreur:d1
> ZREVRANGE livreurs:ratings 0 -1 WITHSCORES
```

### Vérification MongoDB
```bash
# Via MongoDB Compass
# Connexion: mongodb+srv://user:pass@cluster.mongodb.net/

# Collections à vérifier:
- deliveries_db.deliveries (6+ documents)
- Index sur driver_id
- Index composé sur region+delivery_time
```

---

## Performances

### Redis

- **Latence moyenne** : < 1ms
- **Throughput** : > 100k ops/sec
- **Structures optimisées** : O(log n) pour Sorted Sets

### MongoDB

- **Index simples** : O(log n) pour les recherches
- **Index composés** : Optimisent les requêtes multi-champs
- **Agrégations** : Pipeline optimisé par MongoDB

---

## Améliorations Possibles

1. **Redis Pub/Sub** : Notifications temps réel des changements
2. **Redis Streams** : Queue de messages pour synchronisation
3. **MongoDB Change Streams** : Écoute des modifications
4. **Sharding MongoDB** : Distribution des données
5. **Redis Cluster** : Haute disponibilité
6. **API REST** : Exposition des fonctionnalités
7. **Tests unitaires** : Couverture avec pytest

---

## Auteurs

Projet réalisé dans le cadre du cours NoSQL - M1 Data Science EFREI (2024-2025)

