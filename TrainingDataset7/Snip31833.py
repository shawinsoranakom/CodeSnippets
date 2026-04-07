def test_view(self):
        with self.urlopen("/example_view/") as f:
            self.assertEqual(f.read(), b"example view")