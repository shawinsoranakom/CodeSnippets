def test_permwrapper_in(self):
        """
        'something' in PermWrapper works as expected.
        """
        perms = PermWrapper(MockUser())
        # Works for modules and full permissions.
        self.assertIn("mockapp", perms)
        self.assertNotIn("nonexistent", perms)
        self.assertIn("mockapp.someperm", perms)
        self.assertNotIn("mockapp.nonexistent", perms)