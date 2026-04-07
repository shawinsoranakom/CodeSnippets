def test_invalid_permission_name(self):
        msg = "Permission name should be in the form app_label.permission_codename."
        for perm in ("nodots", "too.many.dots", "...", ""):
            with self.subTest(perm), self.assertRaisesMessage(ValueError, msg):
                User.objects.with_perm(perm)