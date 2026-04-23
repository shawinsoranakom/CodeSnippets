def test_key_regex(self):
        self.assertIs(
            NullableJSONModel.objects.filter(value__foo__regex=r"^bar$").exists(), True
        )