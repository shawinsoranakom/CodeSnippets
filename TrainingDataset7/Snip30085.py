def assertOIDs(self, oids):
        self.assertIsInstance(oids, tuple)
        self.assertGreater(len(oids), 0)
        self.assertTrue(all(isinstance(oid, int) for oid in oids))