def test_input_types(self):
        # Test valid input types.
        type_strings = ["default", "password"]
        type_values = [TextInput.DEFAULT, TextInput.PASSWORD]
        for type_string, type_value in zip(type_strings, type_values):
            st.text_input("label", type=type_string)

            c = self.get_delta_from_queue().new_element.text_input
            self.assertEqual(type_value, c.type)

        # An invalid input type should raise an exception.
        with self.assertRaises(StreamlitAPIException) as exc:
            st.text_input("label", type="bad_type")

        self.assertEqual(
            "'bad_type' is not a valid text_input type. "
            "Valid types are 'default' and 'password'.",
            str(exc.exception),
        )