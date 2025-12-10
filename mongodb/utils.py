from config.mongodb_config import get_database

def get_deliveries_collection():
    """Retourne la collection deliveries"""
    db = get_database()
    return db["deliveries"]

def reset_collection():
    """Vide la collection (utile pour les tests)"""
    collection = get_deliveries_collection()
    collection.delete_many({})
    print("Collection deliveries réinitialisée")
