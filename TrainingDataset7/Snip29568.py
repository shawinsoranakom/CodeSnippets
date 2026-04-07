def test_exact_charfield(self):
        instance = CharArrayModel.objects.create(field=["text"])
        self.assertSequenceEqual(
            CharArrayModel.objects.filter(field=["text"]), [instance]
        )