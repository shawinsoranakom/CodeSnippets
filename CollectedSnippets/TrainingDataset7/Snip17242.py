def test_filter_alias_with_double_f(self):
        qs = Book.objects.alias(
            other_rating=F("rating"),
        ).filter(other_rating=F("rating"))
        self.assertIs(hasattr(qs.first(), "other_rating"), False)
        self.assertEqual(qs.count(), Book.objects.count())