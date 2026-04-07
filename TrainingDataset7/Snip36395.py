def test_json_script_without_id(self):
        self.assertHTMLEqual(
            json_script({"key": "value"}),
            '<script type="application/json">{"key": "value"}</script>',
        )