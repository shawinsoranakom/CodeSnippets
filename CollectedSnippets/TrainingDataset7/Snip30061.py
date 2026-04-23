def test_headline_highlight_all_option(self):
        self.check_default_text_search_config()
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                "dialogue",
                SearchQuery("brave sir robin", config="english"),
                highlight_all=True,
            ),
        ).get(pk=self.verse0.pk)
        self.assertIn(
            "<b>Bravely</b> bold <b>Sir</b> <b>Robin</b>, rode forth from "
            "Camelot. He was not afraid to die, o ",
            searched.headline,
        )