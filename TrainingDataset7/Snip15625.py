def test_is_registered_model(self):
        "Checks for registered models should return true."
        self.site.register(Person)
        self.assertTrue(self.site.is_registered(Person))