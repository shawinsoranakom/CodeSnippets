def test_has_perm(self):
        self.assertIs(self.user1.has_perm("perm", TestObj()), False)
        self.assertIs(self.user2.has_perm("perm", TestObj()), True)
        self.assertIs(self.user2.has_perm("perm"), False)
        self.assertIs(self.user2.has_perms(["simple", "advanced"], TestObj()), True)
        self.assertIs(self.user3.has_perm("perm", TestObj()), False)
        self.assertIs(self.user3.has_perm("anon", TestObj()), False)
        self.assertIs(self.user3.has_perms(["simple", "advanced"], TestObj()), False)