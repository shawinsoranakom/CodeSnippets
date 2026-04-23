def test_deepcopy(self):
        f = F("foo")
        g = deepcopy(f)
        self.assertEqual(f.name, g.name)