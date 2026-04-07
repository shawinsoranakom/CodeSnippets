def assertFileFound(self, filename):
        # Some temp directories are symlinks. Python resolves these fully while
        # importing.
        resolved_filename = filename.resolve(strict=True)
        self.clear_autoreload_caches()
        # Test uncached access
        self.assertIn(
            resolved_filename, list(autoreload.iter_all_python_module_files())
        )
        # Test cached access
        self.assertIn(
            resolved_filename, list(autoreload.iter_all_python_module_files())
        )
        self.assertEqual(autoreload.iter_modules_and_files.cache_info().hits, 1)