def test_custom_backend_pass_obj(self):
        for perm in ("auth.test", self.permission):
            with self.subTest(perm):
                self.assertSequenceEqual(
                    User.objects.with_perm(perm, obj=self.user_charlie_b),
                    [self.user_charlie_b],
                )