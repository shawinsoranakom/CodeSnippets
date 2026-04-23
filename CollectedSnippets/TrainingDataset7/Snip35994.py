def assertFileNotFound(self, filename):
        resolved_filename = filename.resolve(strict=True)
        self.clear_autoreload_caches()
        # Test uncached access
        self.assertNotIn(
            resolved_filename, list(autoreload.iter_all_python_module_files())
        )
        # Test cached access
        self.assertNotIn(
            resolved_filename, list(autoreload.iter_all_python_module_files())
        )
        self.assertEqual(autoreload.iter_modules_and_files.cache_info().hits, 1)