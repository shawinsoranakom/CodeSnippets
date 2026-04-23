def test_no_engines_configured(self):
        msg = "No DjangoTemplates backend is configured."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            Engine.get_default()