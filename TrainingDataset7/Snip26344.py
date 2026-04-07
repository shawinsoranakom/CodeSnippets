def test_get_prefetch_querysets_invalid_querysets_length(self):
        articles = Article.objects.all()
        msg = (
            "querysets argument of get_prefetch_querysets() should have a length of 1."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.a1.publications.get_prefetch_querysets(
                instances=articles,
                querysets=[Publication.objects.all(), Publication.objects.all()],
            )