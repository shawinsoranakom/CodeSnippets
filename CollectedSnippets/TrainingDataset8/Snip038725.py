def test_cell_styles(self):
        df = mock_data_frame()
        styler = df.style
        # NOTE: If UUID is not set - a random UUID will be generated.
        styler.set_uuid("FAKE_UUID")
        styler.highlight_max(axis=None)
        st._arrow_dataframe(styler)

        proto = self.get_delta_from_queue().new_element.arrow_data_frame
        self.assertEqual(
            proto.styler.styles, "#T_FAKE_UUIDrow1_col2 { background-color: yellow }"
        )