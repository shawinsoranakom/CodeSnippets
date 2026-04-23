def tearDown(self):
        for p in self.patches:
            p.stop()