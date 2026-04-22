def test_set_page_config_menu_items_empty_dict(self):
        st.set_page_config(menu_items={})
        c = self.get_message_from_queue().page_config_changed.menu_items
        self.assertEqual(c.about_section_md, "")