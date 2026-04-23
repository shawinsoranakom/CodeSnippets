def test_config_query_implicit(self):
        searched = Line.objects.annotate(
            search=SearchVector("scene__setting", "dialogue", config="french"),
        ).filter(search="cadeaux")
        self.assertSequenceEqual(searched, [self.french])