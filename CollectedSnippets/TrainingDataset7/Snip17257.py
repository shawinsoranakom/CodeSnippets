def setUp(self):
        self.egg_dir = "%s/eggs" % os.path.dirname(__file__)
        self.addCleanup(apps.clear_cache)