"""
PARTIE 4 : Geo-spatial (Localisation en temps reel)
Gestion de la localisation GPS des livreurs et recherche par proximite
"""
import redis
import sys
import os

# Ajouter le chemin parent pour importer la config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import REDIS_CONFIG

# Connexion Redis
r = redis.Redis(**REDIS_CONFIG)

def reset_redis():
    """Nettoie toutes les donnees Redis pour recommencer proprement"""
    r.flushdb()
    print("[RESET] Base Redis nettoyee")

def initialiser_donnees_base():
    """Initialise les livreurs avec leurs donnees de base"""
    print("\n[INIT] Initialisation des livreurs")
    
    livreurs = [
        {"id": "d1", "nom": "Alice Dupont", "region": "Paris", "rating": 4.8},
        {"id": "d2", "nom": "Bob Martin", "region": "Paris", "rating": 4.5},
        {"id": "d3", "nom": "Charlie Lefevre", "region": "Banlieue", "rating": 4.9},
        {"id": "d4", "nom": "Diana Russo", "region": "Banlieue", "rating": 4.3},
    ]
    
    for livreur in livreurs:
        r.hset(f"livreur:{livreur['id']}", mapping={
            "nom": livreur["nom"],
            "region": livreur["region"],
            "rating": livreur["rating"]
        })
        r.zadd("livreurs:ratings", {livreur["id"]: livreur["rating"]})
        print(f"[OK] {livreur['id']} ({livreur['nom']}) - Rating: {livreur['rating']}")

def travail1_stocker_positions():
    """
    Travail 1 : Stocker les positions geo-spatiales
    
    Utilisation de GEOADD pour stocker :
    - Les lieux de livraison
    - Les positions actuelles des livreurs
    """
    print("\n\n[TRAVAIL 1] Stocker les positions geo-spatiales")
    
    # Lieux de livraison avec coordonnees GPS (longitude, latitude)
    print("\n--- Lieux de livraison ---")
    lieux = [
        {"nom": "Marais", "region": "Paris", "lon": 2.364, "lat": 48.861},
        {"nom": "Belleville", "region": "Paris", "lon": 2.379, "lat": 48.870},
        {"nom": "Bercy", "region": "Paris", "lon": 2.381, "lat": 48.840},
        {"nom": "Auteuil", "region": "Paris", "lon": 2.254, "lat": 48.851},
    ]
    
    for lieu in lieux:
        r.geoadd("delivery_points", (lieu["lon"], lieu["lat"], lieu["nom"]))
        print(f"[OK] {lieu['nom']}: ({lieu['lon']}, {lieu['lat']})")
    
    # Positions actuelles des livreurs
    print("\n--- Positions des livreurs ---")
    positions = [
        {"id": "d1", "region": "Paris", "lon": 2.365, "lat": 48.862},
        {"id": "d2", "region": "Paris", "lon": 2.378, "lat": 48.871},
        {"id": "d3", "region": "Banlieue", "lon": 2.320, "lat": 48.920},
        {"id": "d4", "region": "Banlieue", "lon": 2.400, "lat": 48.750},
    ]
    
    for pos in positions:
        r.geoadd("drivers_locations", (pos["lon"], pos["lat"], pos["id"]))
        nom = r.hget(f"livreur:{pos['id']}", "nom")
        print(f"[OK] {pos['id']} ({nom}): ({pos['lon']}, {pos['lat']})")
    
    print("\n[INFO] Utilisation de la commande GEOADD pour stocker les coordonnees GPS")
    print("Format: GEOADD key longitude latitude member")

def travail2_trouver_livreurs_proches():
    """
    Travail 2 : Trouver les livreurs proches d'un lieu
    
    Utilisation de :
    - GEORADIUS : chercher dans un rayon
    - GEODIST : calculer la distance entre deux points
    """
    print("\n\n[TRAVAIL 2] Trouver les livreurs proches")
    
    lieu = "Marais"
    
    # 1. Tous les livreurs dans un rayon de 2 km
    print(f"\n--- Livreurs dans un rayon de 2 km autour du {lieu} ---")
    
    # Recuperer les coordonnees du Marais
    coords_marais = r.geopos("delivery_points", lieu)[0]
    if coords_marais:
        lon_marais, lat_marais = coords_marais
        
        # Chercher les livreurs dans un rayon de 2 km
        livreurs_proches = r.georadius(
            "drivers_locations",
            lon_marais,
            lat_marais,
            2,
            unit="km"
        )
        
        print(f"Nombre de livreurs trouves : {len(livreurs_proches)}")
        for lid in livreurs_proches:
            nom = r.hget(f"livreur:{lid}", "nom")
            print(f"  - {lid}: {nom}")
    
    # 2. Livreurs avec distance exacte
    print(f"\n--- Livreurs avec distance au {lieu} ---")
    
    livreurs_avec_distance = r.georadius(
        "drivers_locations",
        lon_marais,
        lat_marais,
        2,
        unit="km",
        withdist=True,
        sort="ASC"
    )
    
    for lid, distance in livreurs_avec_distance:
        nom = r.hget(f"livreur:{lid}", "nom")
        rating = r.hget(f"livreur:{lid}", "rating")
        print(f"  - {lid} ({nom}): {distance:.2f} km - Rating: {rating}")
    
    # 3. Les 2 livreurs les plus proches
    print(f"\n--- Les 2 livreurs les plus proches du {lieu} ---")
    
    top2_proches = r.georadius(
        "drivers_locations",
        lon_marais,
        lat_marais,
        10,
        unit="km",
        withdist=True,
        count=2,
        sort="ASC"
    )
    
    for lid, distance in top2_proches:
        nom = r.hget(f"livreur:{lid}", "nom")
        rating = r.hget(f"livreur:{lid}", "rating")
        print(f"  - {lid} ({nom}): {distance:.2f} km - Rating: {rating}")

def travail3_affectation_optimale():
    """
    Travail 3 : Cas d'usage - Affectation optimale
    
    Trouver le meilleur livreur pour une commande au Marais en combinant :
    - Proximite (distance)
    - Rating
    """
    print("\n\n[TRAVAIL 3] Affectation optimale d'une commande")
    
    lieu = "Marais"
    rayon_max = 3  # km
    
    print(f"\nNouvelle commande au {lieu}")
    print(f"Criteres : Rayon max {rayon_max} km, meilleur rating possible")
    
    # Recuperer coordonnees du Marais
    coords = r.geopos("delivery_points", lieu)[0]
    if not coords:
        print("[ERREUR] Lieu non trouve")
        return
    
    lon, lat = coords
    
    # Chercher tous les livreurs dans le rayon
    livreurs_disponibles = r.georadius(
        "drivers_locations",
        lon,
        lat,
        rayon_max,
        unit="km",
        withdist=True
    )
    
    print(f"\n--- Livreurs disponibles dans un rayon de {rayon_max} km ---")
    
    candidats = []
    for lid, distance in livreurs_disponibles:
        nom = r.hget(f"livreur:{lid}", "nom")
        rating = float(r.hget(f"livreur:{lid}", "rating"))
        
        candidats.append({
            "id": lid,
            "nom": nom,
            "distance": distance,
            "rating": rating
        })
        
        print(f"  - {lid} ({nom}): {distance:.2f} km, Rating: {rating}")
    
    if not candidats:
        print("\n[RESULTAT] Aucun livreur disponible")
        return
    
    # Strategie 1 : Le plus proche
    plus_proche = min(candidats, key=lambda x: x["distance"])
    print(f"\n--- Strategie 1 : Le plus proche ---")
    print(f"Livreur selectionne : {plus_proche['id']} ({plus_proche['nom']})")
    print(f"Distance : {plus_proche['distance']:.2f} km, Rating: {plus_proche['rating']}")
    
    # Strategie 2 : Le mieux note
    mieux_note = max(candidats, key=lambda x: x["rating"])
    print(f"\n--- Strategie 2 : Le mieux note ---")
    print(f"Livreur selectionne : {mieux_note['id']} ({mieux_note['nom']})")
    print(f"Distance : {mieux_note['distance']:.2f} km, Rating: {mieux_note['rating']}")
    
    # Strategie 3 : Equilibre (score combine)
    # Score = rating / distance (favorise bon rating et proximite)
    for candidat in candidats:
        candidat["score"] = candidat["rating"] / max(candidat["distance"], 0.1)
    
    meilleur_equilibre = max(candidats, key=lambda x: x["score"])
    print(f"\n--- Strategie 3 : Meilleur equilibre (rating/distance) ---")
    print(f"Livreur selectionne : {meilleur_equilibre['id']} ({meilleur_equilibre['nom']})")
    print(f"Distance : {meilleur_equilibre['distance']:.2f} km, Rating: {meilleur_equilibre['rating']}")
    print(f"Score : {meilleur_equilibre['score']:.2f}")

def travail4_monitoring_livreurs():
    """
    Travail 4 : Monitoring des livreurs (Bonus avance)
    
    Logique pour :
    - Mettre a jour la position d'un livreur
    - Detecter s'il sort de sa zone
    """
    print("\n\n[TRAVAIL 4] Monitoring des livreurs")
    
    # Centre de Paris (approximatif)
    centre_paris_lon = 2.3522
    centre_paris_lat = 48.8566
    zone_max = 5  # km
    
    print(f"\nCentre de surveillance : Paris ({centre_paris_lon}, {centre_paris_lat})")
    print(f"Rayon de la zone : {zone_max} km")
    
    # Ajouter le centre comme point de reference
    r.geoadd("zones", (centre_paris_lon, centre_paris_lat, "centre_paris"))
    
    # Fonction de mise a jour de position
    print("\n--- Simulation : Mise a jour position d1 ---")
    
    livreur_id = "d1"
    nom = r.hget(f"livreur:{livreur_id}", "nom")
    
    # Position actuelle
    pos_actuelle = r.geopos("drivers_locations", livreur_id)[0]
    print(f"Position actuelle de {livreur_id} ({nom}) : {pos_actuelle}")
    
    # Nouvelle position (se deplace loin)
    nouvelle_lon = 2.450
    nouvelle_lat = 48.950
    
    print(f"Nouvelle position : ({nouvelle_lon}, {nouvelle_lat})")
    
    # Mettre a jour
    r.geoadd("drivers_locations", (nouvelle_lon, nouvelle_lat, livreur_id))
    print(f"[OK] Position mise a jour")
    
    # Verifier quels livreurs sont hors zone
    print(f"\n--- Verification des livreurs hors zone ---")
    
    # Trouver tous les livreurs dans la zone
    livreurs_dans_zone = r.georadius(
        "drivers_locations",
        centre_paris_lon,
        centre_paris_lat,
        zone_max,
        unit="km"
    )
    
    # Tous les livreurs
    tous_livreurs = ["d1", "d2", "d3", "d4"]
    
    for lid in tous_livreurs:
        nom_livreur = r.hget(f"livreur:{lid}", "nom")
        
        # Calculer distance au centre
        r.geoadd("zones", (centre_paris_lon, centre_paris_lat, "centre_paris"))
        
        # Utiliser georadiusbymember pour verifier
        proches = r.georadiusbymember(
            "drivers_locations",
            lid,
            100,  # Grand rayon pour recuperer la distance
            unit="km",
            withdist=True
        )
        
        # Trouver distance au centre manuellement
        pos_livreur = r.geopos("drivers_locations", lid)[0]
        if pos_livreur:
            lon_liv, lat_liv = pos_livreur
            
            # Calculer si dans zone avec georadius
            dans_rayon = r.georadius(
                "drivers_locations",
                centre_paris_lon,
                centre_paris_lat,
                zone_max,
                unit="km"
            )
            
            if lid in dans_rayon:
                print(f"[OK] {lid} ({nom_livreur}) est dans la zone")
            else:
                print(f"[ALERTE] {lid} ({nom_livreur}) est hors de la zone de service")
    
    # Pseudocode pour monitoring en temps reel
    print("\n--- Logique de monitoring temps reel ---")
    print("""
def monitoring_position_livreur(livreur_id, nouvelle_lon, nouvelle_lat):
    # 1. Mettre a jour la position
    r.geoadd("drivers_locations", (nouvelle_lon, nouvelle_lat, livreur_id))
    
    # 2. Verifier si dans la zone de service
    livreurs_dans_zone = r.georadius(
        "drivers_locations",
        centre_lon, centre_lat, rayon_max,
        unit="km"
    )
    
    # 3. Envoyer alerte si hors zone
    if livreur_id not in livreurs_dans_zone:
        envoyer_alerte(f"Livreur {{livreur_id}} hors zone")
        return False
    
    return True

# Appel toutes les 10 secondes pour chaque livreur actif
    """)

if __name__ == "__main__":
    # Nettoyer Redis
    reset_redis()
    
    # Initialiser les donnees
    initialiser_donnees_base()
    
    # Executer les travaux
    travail1_stocker_positions()
    travail2_trouver_livreurs_proches()
    travail3_affectation_optimale()
    travail4_monitoring_livreurs()
    
    print("\n\n[FIN] Partie 4 terminee")