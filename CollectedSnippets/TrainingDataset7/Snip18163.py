def test_custom_backend(self):
        for perm in ("auth.test", self.permission):
            with self.subTest(perm):
                self.assertCountEqual(
                    User.objects.with_perm(perm),
                    [self.user_charlie, self.user_charlie_b],
                )