def test_set_page_config_menu_items_none(self):
        menu_items = {"report a bug": None, "GET HELP": None, "about": None}
        st.set_page_config(menu_items=menu_items)
        c = self.get_message_from_queue().page_config_changed.menu_items
        self.assertTrue(c.hide_report_a_bug)
        self.assertTrue(c.hide_get_help)
        self.assertEqual(c.about_section_md, "")