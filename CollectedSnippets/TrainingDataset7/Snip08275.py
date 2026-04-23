def _list_cache_files(self):
        """
        Get a list of paths to all the cache files. These are all the files
        in the root cache dir that end on the cache_suffix.
        """
        return [
            os.path.join(self._dir, fname)
            for fname in glob.glob(f"*{self.cache_suffix}", root_dir=self._dir)
        ]