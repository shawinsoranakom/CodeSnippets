def test_has_perms(self):
        self.assertIs(self.user1.has_perms(["anon"], TestObj()), True)
        self.assertIs(self.user1.has_perms(["anon", "perm"], TestObj()), False)