def test_set_page_config_sidebar_expanded(self):
        st.set_page_config(initial_sidebar_state="expanded")
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.initial_sidebar_state, PageConfigProto.EXPANDED)