def test_set_page_config_menu_items_bug_and_help(self):
        menu_items = {
            "report a bug": "https://report_a_bug.com",
            "GET HELP": "https://get_help.com",
        }
        st.set_page_config(menu_items=menu_items)
        c = self.get_message_from_queue().page_config_changed.menu_items
        self.assertFalse(c.hide_report_a_bug)
        self.assertFalse(c.hide_get_help)
        self.assertEqual(c.about_section_md, "")
        self.assertEqual(c.report_a_bug_url, "https://report_a_bug.com")
        self.assertEqual(c.get_help_url, "https://get_help.com")