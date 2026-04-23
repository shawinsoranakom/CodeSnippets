def test_set_page_config_sidebar_auto(self):
        st.set_page_config(initial_sidebar_state="auto")
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.initial_sidebar_state, PageConfigProto.AUTO)