def test_key_icontains(self):
        self.assertIs(
            NullableJSONModel.objects.filter(value__foo__icontains="Ar").exists(), True
        )