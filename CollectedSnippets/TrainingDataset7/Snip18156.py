def test_invalid_permission_type(self):
        msg = "The `perm` argument must be a string or a permission instance."
        for perm in (b"auth.test", object(), None):
            with self.subTest(perm), self.assertRaisesMessage(TypeError, msg):
                User.objects.with_perm(perm)