def test_has_module_perms(self):
        self.assertIs(self.user1.has_module_perms("app1"), True)
        self.assertIs(self.user1.has_module_perms("app2"), False)