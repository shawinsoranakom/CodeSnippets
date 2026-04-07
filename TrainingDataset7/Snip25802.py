def test_values_two_fields(self):
        self.assertSequenceEqual(
            Article.objects.values("id", "headline"),
            [
                {"id": self.a5.id, "headline": "Article 5"},
                {"id": self.a6.id, "headline": "Article 6"},
                {"id": self.a4.id, "headline": "Article 4"},
                {"id": self.a2.id, "headline": "Article 2"},
                {"id": self.a3.id, "headline": "Article 3"},
                {"id": self.a7.id, "headline": "Article 7"},
                {"id": self.a1.id, "headline": "Article 1"},
            ],
        )