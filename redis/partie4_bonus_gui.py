import streamlit as st
import redis
import sys
import os
import time
import pandas as pd
import pydeck as pdk
import random
from datetime import datetime

# --- CONFIGURATION DU CHEMIN ---
# Ajouter le chemin parent pour importer la config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config.redis_config import REDIS_CONFIG
except ImportError:
    # Fallback si l'import échoue
    st.error("Impossible d'importer la config Redis. Vérifiez l'emplacement du fichier.")
    st.stop()

# --- CONSTANTES ---
CENTRE_PARIS = {"lon": 2.3522, "lat": 48.8566, "name": "Centre Paris (QG)"}
RAYON_MAX_KM = 5.0
VITESSE_SIMULATION = 0.002  # Degrés de déplacement par tick (simulation)


# --- CONNEXION REDIS ---
@st.cache_resource
def get_redis_client():
    return redis.Redis(**REDIS_CONFIG)


try:
    r = get_redis_client()
    r.ping()
except Exception as e:
    st.error(f"Erreur de connexion Redis : {e}")
    st.stop()


# --- FONCTIONS METIER ---

def init_demo_data():
    """Réinitialise les positions des livreurs pour la démo"""
    r.delete("drivers_locations")

    # Positions initiales
    livreurs_init = [
        ("d1", 2.365, 48.862),  # Paris Centre
        ("d2", 2.378, 48.871),  # Paris Nord
        ("d3", 2.410, 48.890),  # Banlieue (Limite)
        ("d4", 2.320, 48.840),  # Paris Sud
    ]

    for lid, lon, lat in livreurs_init:
        r.geoadd("drivers_locations", (lon, lat, lid))
        if not r.exists(f"livreur:{lid}"):
            r.hset(f"livreur:{lid}", mapping={"nom": f"Livreur {lid.upper()}", "rating": 4.5})


def simuler_deplacement(driver_id, current_lon, current_lat):
    """Simule un déplacement aléatoire"""
    delta_lat = (random.random() - 0.5) * VITESSE_SIMULATION
    delta_lon = (random.random() - 0.5) * VITESSE_SIMULATION

    new_lon = current_lon + delta_lon
    new_lat = current_lat + delta_lat

    r.geoadd("drivers_locations", (new_lon, new_lat, driver_id))
    return new_lon, new_lat


def get_driver_status():
    """Récupère positions, calcule distances et génère le statut."""
    r.geoadd("ref_points", (CENTRE_PARIS["lon"], CENTRE_PARIS["lat"], "center"))

    drivers = r.zrange("drivers_locations", 0, -1)
    data = []

    for d in drivers:
        d_id = d

        if d_id == "center":
            continue

        pos = r.geopos("drivers_locations", d_id)
        if not pos or not pos[0]:
            continue
        lon, lat = pos[0]

        # Calcul distance
        r.geoadd("drivers_locations", (CENTRE_PARIS["lon"], CENTRE_PARIS["lat"], "center"))
        dist = r.geodist("drivers_locations", d_id, "center", unit="km")

        if dist is None: dist = 0

        # Détection hors zone
        is_alert = dist > RAYON_MAX_KM
        nom = r.hget(f"livreur:{d_id}", "nom") or d_id

        data.append({
            "id": d_id,
            "nom": nom,
            "lat": lat,
            "lon": lon,
            "distance": round(dist, 2),
            "status": "🚨 HORS ZONE" if is_alert else "✅ OK",
            "color": [255, 0, 0, 200] if is_alert else [0, 255, 0, 200],
            "size": 200 if is_alert else 100
        })

    if not data:
        return pd.DataFrame(columns=["id", "nom", "lat", "lon", "distance", "status", "color", "size"])

    return pd.DataFrame(data)


# --- INTERFACE GRAPHIQUE (STREAMLIT) ---

st.set_page_config(page_title="Dashboard Livraison Redis", layout="wide")

st.title("🚀 Dashboard Live : Monitoring Livreurs")
st.markdown(f"**Zone de service :** {RAYON_MAX_KM} km autour de Paris Centre")

# Bouton de reset
if st.button("Initialiser / Reset Simulation"):
    init_demo_data()
    st.success("Données réinitialisées !")

# --- CORRECTION PRINCIPALE ICI ---
# On ne définit PAS les colonnes ici. On définit seulement le placeholder.
placeholder = st.empty()

# Boucle de rafraichissement
while True:
    # 1. Mise à jour des positions (Simulation backend)
    drivers_list = r.zrange("drivers_locations", 0, -1)
    for d_id in drivers_list:
        if d_id == "center": continue
        pos = r.geopos("drivers_locations", d_id)[0]
        if pos:
            simuler_deplacement(d_id, pos[0], pos[1])

    # 2. Récupération des données fraîches
    df_drivers = get_driver_status()

    # 3. Rendu Graphique
    # Tout ce qui est dans ce 'with' sera effacé et recréé à chaque boucle
    with placeholder.container():

        # ON CRÉE LES COLONNES ICI, À L'INTÉRIEUR DU CONTAINER
        col_map, col_stats = st.columns([3, 1])

        # --- Colonne de droite : Stats & Alertes ---
        with col_stats:
            st.subheader("📊 État Temps Réel")

            nb_drivers = len(df_drivers)
            # Protection contre le KeyError si le dataframe est vide
            if 'status' in df_drivers.columns:
                nb_alerts = len(df_drivers[df_drivers['status'] == "🚨 HORS ZONE"])
            else:
                nb_alerts = 0

            kpi1, kpi2 = st.columns(2)
            kpi1.metric("Livreurs Actifs", nb_drivers)
            kpi2.metric("Alertes", nb_alerts, delta_color="inverse", delta=nb_alerts if nb_alerts > 0 else None)

            st.divider()
            st.write("### 🚨 Centre de Notifications")

            if 'status' in df_drivers.columns:
                alerts_df = df_drivers[df_drivers['status'] == "🚨 HORS ZONE"]
                if not alerts_df.empty:
                    for _, row in alerts_df.iterrows():
                        st.error(f"ALERTE : {row['nom']} est à {row['distance']}km du centre !")
                else:
                    st.info("Aucune alerte. Tous les livreurs sont dans la zone.")

            st.divider()
            st.write("### 📋 Détails Flotte")
            if not df_drivers.empty and 'status' in df_drivers.columns:
                st.dataframe(df_drivers[["nom", "distance", "status"]], hide_index=True)

        # --- Colonne de gauche : Carte PyDeck ---
        with col_map:
            layer_zone = pdk.Layer(
                "ScatterplotLayer",
                data=[CENTRE_PARIS],
                get_position=["lon", "lat"],
                get_color=[0, 100, 255, 30],
                get_radius=RAYON_MAX_KM * 1000,
                pickable=False,
            )

            layer_center = pdk.Layer(
                "ScatterplotLayer",
                data=[CENTRE_PARIS],
                get_position=["lon", "lat"],
                get_color=[0, 0, 255, 255],
                get_radius=200,
                pickable=True,
            )

            layer_drivers = pdk.Layer(
                "ScatterplotLayer",
                data=df_drivers,
                get_position=["lon", "lat"],
                get_fill_color="color",
                get_radius="size",
                pickable=True,
                auto_highlight=True,
            )

            view_state = pdk.ViewState(
                latitude=CENTRE_PARIS["lat"],
                longitude=CENTRE_PARIS["lon"],
                zoom=11,
                pitch=0,
            )

            st.pydeck_chart(pdk.Deck(
                map_style=None,
                initial_view_state=view_state,
                layers=[layer_zone, layer_center, layer_drivers],
                tooltip={"html": "<b>{nom}</b><br/>Distance: {distance}km<br/>Statut: {status}"}
            ))

    # Pause de 1 seconde avant la prochaine frame
    time.sleep(1)