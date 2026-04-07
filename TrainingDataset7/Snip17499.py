def test_has_perm(self):
        self.assertIs(self.user.has_perm("user_perm"), True)
        self.assertIs(self.user.has_perm("group_perm"), True)
        self.assertIs(self.user.has_perm("other_perm", TestObj()), False)