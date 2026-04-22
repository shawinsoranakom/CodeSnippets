def tearDown(self):
        Credentials._singleton = None

        for p in self.patches:
            p.stop()