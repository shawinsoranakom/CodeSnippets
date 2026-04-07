def test_headline_separator_options(self):
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                "dialogue",
                "brave sir robin",
                start_sel="<span>",
                stop_sel="</span>",
            ),
        ).get(pk=self.verse0.pk)
        self.assertEqual(
            searched.headline,
            "<span>Robin</span>. He was not at all afraid to be killed in "
            "nasty ways. <span>Brave</span>, <span>brave</span>, <span>brave"
            "</span>, <span>brave</span> <span>Sir</span> <span>Robin</span>",
        )