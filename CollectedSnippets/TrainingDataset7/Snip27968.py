def test_integerfield_cleans_valid_string(self):
        f = models.IntegerField()
        self.assertEqual(f.clean("2", None), 2)