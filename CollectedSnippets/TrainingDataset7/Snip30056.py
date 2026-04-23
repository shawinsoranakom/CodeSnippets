def test_headline(self):
        self.check_default_text_search_config()
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                F("dialogue"),
                SearchQuery("brave sir robin"),
                config=SearchConfig("english"),
            ),
        ).get(pk=self.verse0.pk)
        self.assertEqual(
            searched.headline,
            "<b>Robin</b>. He was not at all afraid to be killed in nasty "
            "ways. <b>Brave</b>, <b>brave</b>, <b>brave</b>, <b>brave</b> "
            "<b>Sir</b> <b>Robin</b>",
        )