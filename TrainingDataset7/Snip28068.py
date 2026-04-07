def test_key_startswith(self):
        self.assertIs(
            NullableJSONModel.objects.filter(value__foo__startswith="b").exists(), True
        )