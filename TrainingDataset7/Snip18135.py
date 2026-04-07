def test_empty_username(self):
        with self.assertRaisesMessage(ValueError, "The given username must be set"):
            User.objects.create_user(username="")