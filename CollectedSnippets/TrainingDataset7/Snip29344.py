def test_stop_slicing(self):
        """
        Use the 'stop' part of slicing notation to limit the results.
        """
        self.assertQuerySetEqual(
            Article.objects.order_by("headline")[:2],
            [
                "Article 1",
                "Article 2",
            ],
            attrgetter("headline"),
        )