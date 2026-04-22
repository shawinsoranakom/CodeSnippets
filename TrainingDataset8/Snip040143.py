def test_user_cannot_be_modified_new_key(self):
        """
        Test that an error is raised when try to assign new value to new key.
        """
        with self.assertRaises(StreamlitAPIException) as e:
            st.experimental_user["foo"] = "bar"

        self.assertEqual(str(e.exception), "st.experimental_user cannot be modified")