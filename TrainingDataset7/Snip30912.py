def assert_pickles(self, qs):
        self.assertEqual(list(pickle.loads(pickle.dumps(qs))), list(qs))