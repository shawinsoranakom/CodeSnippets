def test_has_perm(self):
        self.assertIs(self.user1.has_perm("perm", TestObj()), False)
        self.assertIs(self.user1.has_perm("inactive", TestObj()), True)