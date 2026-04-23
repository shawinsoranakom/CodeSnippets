def test_abstract_model(self):
        """
        Exception is raised when trying to register an abstract model.
        Refs #12004.
        """
        msg = "The model Location is abstract, so it cannot be registered with admin."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.site.register(Location)