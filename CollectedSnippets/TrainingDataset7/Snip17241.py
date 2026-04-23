def test_filter_alias_with_f(self):
        qs = Book.objects.alias(
            other_rating=F("rating"),
        ).filter(other_rating=4.5)
        self.assertIs(hasattr(qs.first(), "other_rating"), False)
        self.assertSequenceEqual(qs, [self.b1])