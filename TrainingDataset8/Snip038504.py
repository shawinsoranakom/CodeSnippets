def test_set_page_config_title(self):
        st.set_page_config(page_title="Hello")
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.title, "Hello")