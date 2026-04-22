def test_set_page_config_layout_wide(self):
        st.set_page_config(layout="wide")
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.layout, PageConfigProto.WIDE)