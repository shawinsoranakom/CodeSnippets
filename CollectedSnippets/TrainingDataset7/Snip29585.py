def test_overlap_charfield(self):
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(field__overlap=["text"]), []
        )