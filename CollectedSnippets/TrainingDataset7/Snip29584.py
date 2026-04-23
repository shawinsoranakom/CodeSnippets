def test_contained_by_charfield(self):
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(field__contained_by=["text"]), []
        )