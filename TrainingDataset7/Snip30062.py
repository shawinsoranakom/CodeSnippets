def test_headline_short_word_option(self):
        self.check_default_text_search_config()
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                "dialogue",
                SearchQuery("Camelot", config="english"),
                short_word=5,
                min_words=8,
            ),
        ).get(pk=self.verse0.pk)
        self.assertEqual(
            searched.headline,
            (
                "<b>Camelot</b>. He was not afraid to die, o Brave Sir Robin. He "
                "was not at all afraid"
            ),
        )