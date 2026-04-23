def test_repr(self):
        perms = PermWrapper(MockUser())
        self.assertEqual(repr(perms), "PermWrapper(MockUser())")