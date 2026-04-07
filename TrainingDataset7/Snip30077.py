def test_config_query_explicit(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue", config="french"),
        ).filter(search=SearchQuery(Lexeme("cadeaux"), config="french"))

        self.assertSequenceEqual(searched, [self.french])