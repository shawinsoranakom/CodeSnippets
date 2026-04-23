def test_set_page_config_icon_invalid_string(self):
        """If set_page_config is passed a garbage icon string, we just pass it
        through without an error (even though nothing will be displayed).
        """
        st.set_page_config(page_icon="st.balloons")
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.favicon, "st.balloons")