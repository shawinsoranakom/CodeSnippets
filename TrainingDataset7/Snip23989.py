def test03_aliases(self):
        "Testing driver aliases."
        for alias, full_name in aliases.items():
            dr = Driver(alias)
            self.assertEqual(full_name, str(dr))