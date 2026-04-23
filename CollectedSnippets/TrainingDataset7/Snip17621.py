def test_swappable_user_nonexistent_model(self):
        "The current user model must point to an installed model"
        msg = (
            "AUTH_USER_MODEL refers to model 'thismodel.doesntexist' "
            "that has not been installed"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            get_user_model()