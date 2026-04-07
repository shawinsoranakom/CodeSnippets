def test_multiple_backends(self):
        msg = (
            "You have multiple authentication backends configured and "
            "therefore must provide the `backend` argument."
        )
        with self.assertRaisesMessage(ValueError, msg):
            User.objects.with_perm("auth.test")

        backend = "auth_tests.test_models.CustomModelBackend"
        self.assertCountEqual(
            User.objects.with_perm("auth.test", backend=backend),
            [self.user_charlie, self.user_charlie_b],
        )