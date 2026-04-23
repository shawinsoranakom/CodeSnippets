def test_trigram_word_search(self):
        obj = self.Model.objects.create(
            field="Gumby rides on the path of Middlesbrough",
        )
        self.assertSequenceEqual(
            self.Model.objects.filter(field__trigram_word_similar="Middlesborough"),
            [obj],
        )
        self.assertSequenceEqual(
            self.Model.objects.filter(field__trigram_word_similar="Middle"),
            [obj],
        )