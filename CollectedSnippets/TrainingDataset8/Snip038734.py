def test_table_styles(self):
        df = mock_data_frame()
        styler = df.style
        # NOTE: If UUID is not set - a random UUID will be generated.
        styler.set_uuid("FAKE_UUID")
        styler.set_table_styles(
            [{"selector": ".blank", "props": [("background-color", "red")]}]
        )
        st._arrow_table(styler)

        proto = self.get_delta_from_queue().new_element.arrow_table
        self.assertEqual(
            proto.styler.styles, "#T_FAKE_UUID .blank { background-color: red }"
        )