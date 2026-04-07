def test_missing_kwargs(self):
        msg = "The URL path must contain 'uidb64' and 'token' parameters."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/reset/missing_parameters/")