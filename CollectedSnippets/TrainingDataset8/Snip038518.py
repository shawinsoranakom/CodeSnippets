def test_set_page_config_menu_items_empty_string(self):
        with self.assertRaises(StreamlitAPIException) as e:
            menu_items = {"report a bug": "", "GET HELP": "", "about": ""}
            st.set_page_config(menu_items=menu_items)
        self.assertEqual(str(e.exception), '"" is a not a valid URL!')