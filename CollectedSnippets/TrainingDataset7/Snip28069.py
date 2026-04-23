def test_key_istartswith(self):
        self.assertIs(
            NullableJSONModel.objects.filter(value__foo__istartswith="B").exists(), True
        )