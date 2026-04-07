def test_single_coalesce_expression(self):
        searched = Line.objects.annotate(search=SearchVector("dialogue")).filter(
            search="cadeaux"
        )
        self.assertNotIn("COALESCE(COALESCE", str(searched.query))