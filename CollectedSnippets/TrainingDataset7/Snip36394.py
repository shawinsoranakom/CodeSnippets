def test_json_script_custom_encoder(self):
        class CustomDjangoJSONEncoder(DjangoJSONEncoder):
            def encode(self, o):
                return '{"hello": "world"}'

        self.assertHTMLEqual(
            json_script({}, encoder=CustomDjangoJSONEncoder),
            '<script type="application/json">{"hello": "world"}</script>',
        )