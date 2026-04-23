def test_key_endswith(self):
        self.assertIs(
            NullableJSONModel.objects.filter(value__foo__endswith="r").exists(), True
        )