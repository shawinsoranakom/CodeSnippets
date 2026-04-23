def test_trigram_strict_word_search_matched(self):
        obj = self.Model.objects.create(
            field="Gumby rides on the path of Middlesbrough",
        )
        self.assertSequenceEqual(
            self.Model.objects.filter(
                field__trigram_strict_word_similar="Middlesborough"
            ),
            [obj],
        )
        self.assertSequenceEqual(
            self.Model.objects.filter(field__trigram_strict_word_similar="Middle"),
            [],
        )