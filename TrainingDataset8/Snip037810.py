def clear_all(self) -> None:
        """Clear all in-memory and on-disk caches."""
        with self._caches_lock:
            self._function_caches = {}

            # TODO: Only delete disk cache for functions related to the user's
            #  current script.
            cache_path = get_cache_path()
            if os.path.isdir(cache_path):
                shutil.rmtree(cache_path)