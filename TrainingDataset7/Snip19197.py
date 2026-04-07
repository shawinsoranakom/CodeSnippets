def test_cache_dir_permissions(self):
        os.rmdir(self.dirname)
        dir_path = Path(self.dirname) / "nested" / "filebasedcache"
        for cache_params in settings.CACHES.values():
            cache_params["LOCATION"] = dir_path
        setting_changed.send(self.__class__, setting="CACHES", enter=False)
        cache.set("foo", "bar")
        self.assertIs(dir_path.exists(), True)
        tests = [
            dir_path,
            dir_path.parent,
            dir_path.parent.parent,
        ]
        for directory in tests:
            with self.subTest(directory=directory):
                dir_mode = directory.stat().st_mode & 0o777
                self.assertEqual(dir_mode, 0o700)