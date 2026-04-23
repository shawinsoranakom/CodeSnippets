def test_does_not_shadow_exception(self):
        # Prepare a request object
        request = HttpRequest()
        request.session = self.client.session

        msg = (
            "AUTH_USER_MODEL refers to model 'thismodel.doesntexist' "
            "that has not been installed"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            get_user(request)