def test_seed_display(self):
        shuffler = Shuffler(100)
        shuffler.seed_source = "test"
        self.assertEqual(shuffler.seed_display, "100 (test)")