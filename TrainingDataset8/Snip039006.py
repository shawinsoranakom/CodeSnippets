def test_warns_on_float_type_with_int_format(self):
        st.number_input("the label", value=5.0, format="%d")

        c = self.get_delta_from_queue(-2).new_element.alert
        self.assertEqual(c.format, AlertProto.WARNING)
        self.assertEqual(
            c.body,
            "Warning: NumberInput value below has type float, but format %d displays as integer.",
        )