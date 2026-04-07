def test_stop_start_slicing(self):
        """
        Use the 'stop' and 'start' parts of slicing notation to offset the
        result list.
        """
        self.assertQuerySetEqual(
            Article.objects.order_by("headline")[1:3],
            [
                "Article 2",
                "Article 3",
            ],
            attrgetter("headline"),
        )