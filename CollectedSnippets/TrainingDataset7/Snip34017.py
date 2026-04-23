def test_url20(self):
        output = self.engine.render_to_string(
            "url20", {"client": {"id": 1}, "url_name_in_var": "named.client"}
        )
        self.assertEqual(output, "/named-client/1/")