def test_headline_with_config_from_field(self):
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                "dialogue",
                SearchQuery("cadeaux", config=F("dialogue_config")),
                config=F("dialogue_config"),
            ),
        ).get(pk=self.french.pk)
        self.assertEqual(
            searched.headline,
            "Oh. Un beau <b>cadeau</b>. Oui oui.",
        )