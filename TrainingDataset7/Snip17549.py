def test_has_perms_perm_list_invalid(self):
        msg = "perm_list must be an iterable of permissions."
        with self.assertRaisesMessage(ValueError, msg):
            self.user1.has_perms("perm")
        with self.assertRaisesMessage(ValueError, msg):
            self.user1.has_perms(object())