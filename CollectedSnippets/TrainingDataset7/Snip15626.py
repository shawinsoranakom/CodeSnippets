def test_is_registered_not_registered_model(self):
        "Checks for unregistered models should return false."
        self.assertFalse(self.site.is_registered(Person))