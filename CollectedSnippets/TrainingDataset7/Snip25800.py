def test_values_single_field(self):
        self.assertSequenceEqual(
            Article.objects.values("headline"),
            [
                {"headline": "Article 5"},
                {"headline": "Article 6"},
                {"headline": "Article 4"},
                {"headline": "Article 2"},
                {"headline": "Article 3"},
                {"headline": "Article 7"},
                {"headline": "Article 1"},
            ],
        )