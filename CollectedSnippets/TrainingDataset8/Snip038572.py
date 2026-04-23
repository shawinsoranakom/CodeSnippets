def test_set_user_option_scriptable(self):
        """Test that scriptable options can be set from API."""
        # This is set in lib/tests/conftest.py to off
        self.assertEqual(True, config.get_option("client.displayEnabled"))

        try:
            # client.displayEnabled and client.caching can be set after run starts.
            config.set_user_option("client.displayEnabled", False)
            self.assertEqual(False, config.get_option("client.displayEnabled"))
        finally:
            # Restore original value
            config.set_user_option("client.displayEnabled", True)