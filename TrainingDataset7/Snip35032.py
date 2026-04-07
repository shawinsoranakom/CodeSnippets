def test_init_no_seed_argument(self):
        with mock.patch("random.randint", return_value=300):
            shuffler = Shuffler()
        self.assertEqual(shuffler.seed, 300)
        self.assertEqual(shuffler.seed_source, "generated")