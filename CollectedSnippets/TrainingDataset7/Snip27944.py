def test_default_value(self):
        """
        The default value for an ImageField is an instance of
        the field's attr_class (TestImageFieldFile in this case) with no
        name (name set to None).
        """
        p = self.PersonModel()
        self.assertIsInstance(p.mugshot, TestImageFieldFile)
        self.assertFalse(p.mugshot)