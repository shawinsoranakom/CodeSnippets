def test_lookup_int_as_str(self):
        # Integer value can be queried using string
        self.assertSequenceEqual(
            Article.objects.filter(id__iexact=str(self.a1.id)),
            [self.a1],
        )