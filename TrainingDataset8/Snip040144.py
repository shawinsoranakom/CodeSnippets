def test_user_cannot_be_modified_existing_attr(self):
        """
        Test that an error is raised when try to assign new value to existing attr.
        """
        with self.assertRaises(StreamlitAPIException) as e:
            st.experimental_user.email = "bar"

        self.assertEqual(str(e.exception), "st.experimental_user cannot be modified")