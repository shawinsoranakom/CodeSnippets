def test_get_all_articles_for_an_author(self):
        self.assertQuerySetEqual(
            self.a1.article_set.all(),
            [
                "Django lets you build web apps easily",
            ],
            lambda a: a.headline,
        )