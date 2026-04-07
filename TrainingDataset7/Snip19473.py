def test_name_with_colon(self):
        result = check_url_config(None)
        self.assertEqual(len(result), 1)
        warning = result[0]
        self.assertEqual(warning.id, "urls.W003")
        expected_msg = (
            "Your URL pattern '^$' [name='name_with:colon'] has a name including a ':'."
        )
        self.assertIn(expected_msg, warning.msg)