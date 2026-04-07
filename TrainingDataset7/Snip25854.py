def test_exact_exists(self):
        qs = Article.objects.filter(pk=OuterRef("pk"))
        seasons = Season.objects.annotate(pk_exists=Exists(qs)).filter(
            pk_exists=Exists(qs),
        )
        self.assertCountEqual(seasons, Season.objects.all())