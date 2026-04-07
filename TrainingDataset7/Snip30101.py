def test_trigram_concat_precedence(self):
        search_term = "im matthew"
        self.assertSequenceEqual(
            self.Model.objects.annotate(
                concat_result=Concat(
                    Value("I'm "),
                    F("field"),
                    output_field=self.Model._meta.get_field("field"),
                ),
            )
            .filter(concat_result__trigram_similar=search_term)
            .values("field"),
            [{"field": "Matthew"}],
        )