def test_caption(self):
        df = mock_data_frame()
        styler = df.style
        styler.set_caption("FAKE_CAPTION")
        st._arrow_dataframe(styler)

        proto = self.get_delta_from_queue().new_element.arrow_data_frame
        self.assertEqual(proto.styler.caption, "FAKE_CAPTION")