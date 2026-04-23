def test_set_user_option_unscriptable(self):
        """Test that unscriptable options cannot be set with st.set_option."""
        # This is set in lib/tests/conftest.py to off
        self.assertEqual(True, config.get_option("server.enableCORS"))

        with self.assertRaises(StreamlitAPIException):
            config.set_user_option("server.enableCORS", False)