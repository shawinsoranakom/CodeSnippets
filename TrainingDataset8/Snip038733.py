def test_caption(self):
        df = mock_data_frame()
        styler = df.style
        styler.set_caption("FAKE_CAPTION")
        st._arrow_table(styler)

        proto = self.get_delta_from_queue().new_element.arrow_table
        self.assertEqual(proto.styler.caption, "FAKE_CAPTION")