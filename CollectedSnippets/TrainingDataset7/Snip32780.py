def test_backend_improperly_configured(self):
        """
        Failing to initialize a backend keeps raising the original exception
        (#24265).
        """
        msg = "app_dirs must not be set when loaders is defined."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            engines.all()
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            engines.all()