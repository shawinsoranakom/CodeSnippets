def test_contains_charfield(self):
        # Regression for #22907
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(field__contains=["text"]), []
        )