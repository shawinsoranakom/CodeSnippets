def test_headline_fragments_words_options(self):
        self.check_default_text_search_config()
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                "dialogue",
                SearchQuery("brave sir robin", config="english"),
                fragment_delimiter="...<br>",
                max_fragments=4,
                max_words=3,
                min_words=1,
            ),
        ).get(pk=self.verse0.pk)
        self.assertEqual(
            searched.headline,
            "<b>Sir</b> <b>Robin</b>, rode...<br>"
            "<b>Brave</b> <b>Sir</b> <b>Robin</b>...<br>"
            "<b>Brave</b>, <b>brave</b>, <b>brave</b>...<br>"
            "<b>brave</b> <b>Sir</b> <b>Robin</b>",
        )