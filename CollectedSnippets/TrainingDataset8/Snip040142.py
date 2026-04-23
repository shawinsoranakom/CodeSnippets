def test_user_cannot_be_modified_existing_key(self):
        """
        Test that an error is raised when try to assign new value to existing key.
        """
        with self.assertRaises(StreamlitAPIException) as e:
            st.experimental_user["email"] = "NEW_VALUE"

        self.assertEqual(str(e.exception), "st.experimental_user cannot be modified")