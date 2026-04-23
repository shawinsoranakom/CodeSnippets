def test_uppercase_isolation_level(self):
        # Upper case values are also accepted in 'isolation_level'.
        with get_connection() as new_connection:
            new_connection.settings_dict["OPTIONS"][
                "isolation_level"
            ] = self.other_isolation_level.upper()
            self.assertEqual(
                self.get_isolation_level(new_connection),
                self.isolation_values[self.other_isolation_level],
            )