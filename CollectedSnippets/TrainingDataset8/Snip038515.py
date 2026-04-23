def test_set_page_config_sidebar_invalid(self):
        with self.assertRaises(StreamlitAPIException) as e:
            st.set_page_config(initial_sidebar_state="INVALID")
        self.assertEqual(
            str(e.exception),
            '`initial_sidebar_state` must be "auto" or "expanded" or "collapsed" (got "INVALID")',
        )