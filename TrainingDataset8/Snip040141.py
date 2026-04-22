def test_user_non_existing_key(self):
        """Test that an error is raised when called non existed key."""
        with self.assertRaises(KeyError):
            st.write(st.experimental_user["key"])