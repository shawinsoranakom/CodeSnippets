def test_constructor_default_values(self):
        key = "mysection.myName"
        c = ConfigOption(key)
        self.assertEqual("mysection", c.section)
        self.assertEqual("myName", c.name)
        self.assertEqual(None, c.description)
        self.assertEqual("visible", c.visibility)