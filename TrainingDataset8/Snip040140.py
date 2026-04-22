def test_user_non_existing_attr(self):
        """Test that an error is raised when called non existed attr."""
        with self.assertRaises(AttributeError):
            st.write(st.experimental_user.attribute)