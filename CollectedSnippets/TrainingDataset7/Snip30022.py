def test_search_with_non_text(self):
        searched = Line.objects.annotate(
            search=SearchVector("id"),
        ).filter(search=str(self.crowd.id))
        self.assertSequenceEqual(searched, [self.crowd])