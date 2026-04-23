def test_class_fixtures(self):
        "Test cases can load fixture objects into models defined in packages"
        self.assertQuerySetEqual(
            Article.objects.all(),
            [
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker has no place on ESPN",
            ],
            lambda a: a.headline,
        )