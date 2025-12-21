from helpers.config import get_settings, Settings
import os

class BaseController:

    def __init__(self):
        self.config: Settings = get_settings
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        self.database_dir = os.path.join(self.base_dir, "assets/database")
        self.cache_dir = os.path.join(self.base_dir, "assets/cache")
    
    def get_database_path(self, db_name: str):

        database_path = os.path.join(self.database_dir, db_name)

        if not os.path.exists(database_path):
            os.makedirs(database_path, exist_ok=True)
        
        return database_path
    
    def get_cache_path(self, cache_name: str):

        cache_path = os.path.join(self.cache_dir, cache_name)

        if not os.path.exists(cache_path):
            os.makedirs(cache_path, exist_ok=True)
        
        return cache_path