def test_set_page_config_icon_random(self):
        """If page_icon == "random", we choose a random emoji."""
        st.set_page_config(page_icon="random")
        c = self.get_message_from_queue().page_config_changed
        self.assertIn(c.favicon, set(RANDOM_EMOJIS + ENG_EMOJIS))
        self.assertTrue(is_emoji(c.favicon))