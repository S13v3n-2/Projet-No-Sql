from pymongo import MongoClient

def get_mongo_client():
    """Retourne un client MongoDB"""
    # Option locale/Docker
    client = MongoClient("mongodb+srv://haciyilmazer_db_user:haci@datanosql.velxj56.mongodb.net/")
    
    # OU Option Atlas (remplace par ton URI)
    # client = MongoClient("mongodb+srv://username:password@cluster.mongodb.net/")
    
    return client

def get_database():
    """Retourne la base de données du projet"""
    client = get_mongo_client()
    return client["deliveries_db"]
