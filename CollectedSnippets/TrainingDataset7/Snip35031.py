def test_init_none_seed(self):
        with mock.patch("random.randint", return_value=200):
            shuffler = Shuffler(None)
        self.assertEqual(shuffler.seed, 200)
        self.assertEqual(shuffler.seed_source, "generated")