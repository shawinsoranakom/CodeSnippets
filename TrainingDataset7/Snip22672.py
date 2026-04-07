def test_slugfield_normalization(self):
        f = SlugField()
        self.assertEqual(f.clean("    aa-bb-cc    "), "aa-bb-cc")