def test_headline_with_config(self):
        searched = Line.objects.annotate(
            headline=SearchHeadline(
                "dialogue",
                SearchQuery("cadeaux", config="french"),
                config="french",
            ),
        ).get(pk=self.french.pk)
        self.assertEqual(
            searched.headline,
            "Oh. Un beau <b>cadeau</b>. Oui oui.",
        )