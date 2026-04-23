def test_valid_keys(self, key, section, name):
        c = ConfigOption(key)
        self.assertEqual(section, c.section)
        self.assertEqual(name, c.name)