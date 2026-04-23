def test_empty(self):
        with self.assertRaisesMessage(ValueError, "Lexeme value cannot be empty."):
            Line.objects.annotate(
                search=SearchVector("scene__setting", "dialogue")
            ).filter(search=SearchQuery(Lexeme("")))