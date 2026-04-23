def test_uuid(self):
        df = mock_data_frame()
        styler = df.style
        styler.set_uuid("FAKE_UUID")
        st._arrow_table(styler)

        proto = self.get_delta_from_queue().new_element.arrow_table
        self.assertEqual(proto.styler.uuid, "FAKE_UUID")