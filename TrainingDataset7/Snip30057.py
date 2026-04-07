def test_headline_untyped_args(self):
        self.check_default_text_search_config()
        searched = Line.objects.annotate(
            headline=SearchHeadline("dialogue", "killed", config="english"),
        ).get(pk=self.verse0.pk)
        self.assertEqual(
            searched.headline,
            "Robin. He was not at all afraid to be <b>killed</b> in nasty "
            "ways. Brave, brave, brave, brave Sir Robin",
        )