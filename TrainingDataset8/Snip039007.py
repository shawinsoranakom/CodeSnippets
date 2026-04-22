def test_warns_on_int_type_with_float_format(self):
        st.number_input("the label", value=5, format="%0.2f")

        c = self.get_delta_from_queue(-2).new_element.alert
        self.assertEqual(c.format, AlertProto.WARNING)
        self.assertEqual(
            c.body,
            "Warning: NumberInput value below has type int so is displayed as int despite format string %0.2f.",
        )