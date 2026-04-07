def test_create_super_user_raises_error_on_false_is_superuser(self):
        with self.assertRaisesMessage(
            ValueError, "Superuser must have is_superuser=True."
        ):
            User.objects.create_superuser(
                username="test",
                email="test@test.com",
                password="test",
                is_superuser=False,
            )