def test_init(self):
        shuffler = Shuffler(100)
        self.assertEqual(shuffler.seed, 100)
        self.assertEqual(shuffler.seed_source, "given")