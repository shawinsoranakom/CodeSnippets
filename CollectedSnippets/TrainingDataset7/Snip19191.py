def tearDown(self):
        super().tearDown()
        # Call parent first, as cache.clear() may recreate cache base directory
        shutil.rmtree(self.dirname)