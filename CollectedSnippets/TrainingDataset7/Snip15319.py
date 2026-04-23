def test_no_auth_middleware(self):
        msg = (
            "The XView middleware requires authentication middleware to be "
            "installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.head("/xview/func/")