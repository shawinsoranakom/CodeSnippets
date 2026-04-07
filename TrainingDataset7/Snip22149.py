def test_class_fixtures(self):
        "Test case has installed 3 fixture objects"
        self.assertSequenceEqual(
            Article.objects.values_list("headline", flat=True),
            [
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker has no place on ESPN",
            ],
        )