def test_setting_isolation_level(self):
        with get_connection() as new_connection:
            new_connection.settings_dict["OPTIONS"][
                "isolation_level"
            ] = self.other_isolation_level
            self.assertEqual(
                self.get_isolation_level(new_connection),
                self.isolation_values[self.other_isolation_level],
            )