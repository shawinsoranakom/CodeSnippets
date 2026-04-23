def test_values_iterator(self):
        # You can use values() with iterator() for memory savings,
        # because iterator() uses database-level iteration.
        self.assertSequenceEqual(
            list(Article.objects.values("id", "headline").iterator()),
            [
                {"headline": "Article 5", "id": self.a5.id},
                {"headline": "Article 6", "id": self.a6.id},
                {"headline": "Article 4", "id": self.a4.id},
                {"headline": "Article 2", "id": self.a2.id},
                {"headline": "Article 3", "id": self.a3.id},
                {"headline": "Article 7", "id": self.a7.id},
                {"headline": "Article 1", "id": self.a1.id},
            ],
        )