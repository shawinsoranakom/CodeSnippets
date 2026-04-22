def test_set_page_config_icon_calls_image_to_url(self, icon: PageIcon):
        """For all other page_config icon inputs, we just call image_to_url."""
        with mock.patch(
            "streamlit.commands.page_config.image.image_to_url",
            return_value="https://mock.url",
        ):
            st.set_page_config(page_icon=icon)
            c = self.get_message_from_queue().page_config_changed
            self.assertEqual(c.favicon, "https://mock.url")