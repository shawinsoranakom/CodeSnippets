def test_str(self):
        g = Group(name="Users")
        self.assertEqual(str(g), "Users")