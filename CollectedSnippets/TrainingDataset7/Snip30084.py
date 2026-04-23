def test_non_string_values(self):
        msg = "Lexeme value must be a string, got NoneType."
        with self.assertRaisesMessage(TypeError, msg):
            Line.objects.annotate(
                search=SearchVector("scene__setting", "dialogue")
            ).filter(search=SearchQuery(Lexeme(None)))