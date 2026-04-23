def test_in_ignore_solo_none(self):
        with self.assertNumQueries(0):
            self.assertSequenceEqual(Article.objects.filter(id__in=[None]), [])