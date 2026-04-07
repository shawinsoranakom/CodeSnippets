def test_filter_by_reverse_related_field_transform(self):
        fk_field = Article._meta.get_field("author")
        with register_lookup(fk_field, Abs):
            self.assertSequenceEqual(
                Author.objects.filter(article__abs=self.a1.pk), [self.au1]
            )