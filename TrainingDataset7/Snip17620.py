def test_swappable_user_bad_setting(self):
        """
        The alternate user setting must point to something in the format
        app.model
        """
        msg = "AUTH_USER_MODEL must be of the form 'app_label.model_name'"
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            get_user_model()