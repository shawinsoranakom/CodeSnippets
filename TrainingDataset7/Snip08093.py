def clear_cache(self):
        """Clear the ``Site`` object cache."""
        global SITE_CACHE
        SITE_CACHE = {}