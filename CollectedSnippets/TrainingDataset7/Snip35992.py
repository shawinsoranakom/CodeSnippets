def clear_autoreload_caches(self):
        autoreload.iter_modules_and_files.cache_clear()