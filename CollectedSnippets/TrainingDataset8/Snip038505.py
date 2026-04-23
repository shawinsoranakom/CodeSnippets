def test_set_page_config_icon_strings(self, icon_string: str):
        """page_config icons can be emojis, emoji shortcodes, and image URLs."""
        st.set_page_config(page_icon=icon_string)
        c = self.get_message_from_queue().page_config_changed
        self.assertEqual(c.favicon, icon_string)