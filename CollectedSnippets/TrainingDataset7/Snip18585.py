def test_default_isolation_level(self):
        # If not specified in settings, the default is read committed.
        with get_connection() as new_connection:
            new_connection.settings_dict["OPTIONS"].pop("isolation_level", None)
            self.assertEqual(
                self.get_isolation_level(new_connection),
                self.isolation_values[self.read_committed],
            )