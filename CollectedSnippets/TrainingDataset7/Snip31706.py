def test_lazy_string_encoding(self):
        self.assertEqual(
            json.dumps({"lang": gettext_lazy("French")}, cls=DjangoJSONEncoder),
            '{"lang": "French"}',
        )
        with override("fr"):
            self.assertEqual(
                json.dumps({"lang": gettext_lazy("French")}, cls=DjangoJSONEncoder),
                '{"lang": "Fran\\u00e7ais"}',
            )