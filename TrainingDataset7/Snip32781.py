def test_backend_names_must_be_unique(self):
        msg = (
            "Template engine aliases aren't unique, duplicates: django. Set "
            "a unique NAME for each engine in settings.TEMPLATES."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            engines.all()