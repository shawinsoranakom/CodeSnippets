def test_has_perms_perm_list_invalid(self):
        msg = "perm_list must be an iterable of permissions."
        with self.assertRaisesMessage(ValueError, msg):
            self.user.has_perms("user_perm")
        with self.assertRaisesMessage(ValueError, msg):
            self.user.has_perms(object())