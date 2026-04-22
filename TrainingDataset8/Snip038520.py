def test_set_page_config_menu_items_invalid(self):
        with self.assertRaises(StreamlitAPIException) as e:
            menu_items = {"invalid": "fdsa"}
            st.set_page_config(menu_items=menu_items)
        self.assertEqual(
            str(e.exception),
            'We only accept the keys: "Get help", "Report a bug", and "About" '
            '("invalid" is not a valid key.)',
        )