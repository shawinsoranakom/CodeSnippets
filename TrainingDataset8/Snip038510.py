def test_set_page_config_layout_centered(self):
        st.set_page_config(layout="centered")
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.layout, PageConfigProto.CENTERED)