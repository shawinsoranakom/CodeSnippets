def test_isnull_non_boolean_value(self):
        msg = "The QuerySet value for an isnull lookup must be True or False."
        tests = [
            Author.objects.filter(alias__isnull=1),
            Article.objects.filter(author__isnull=1),
            Season.objects.filter(games__isnull=1),
            Freebie.objects.filter(stock__isnull=1),
        ]
        for qs in tests:
            with self.subTest(qs=qs):
                with self.assertRaisesMessage(ValueError, msg):
                    qs.exists()