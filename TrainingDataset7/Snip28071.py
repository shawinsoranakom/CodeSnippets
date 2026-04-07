def test_key_iendswith(self):
        self.assertIs(
            NullableJSONModel.objects.filter(value__foo__iendswith="R").exists(), True
        )