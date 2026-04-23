def test_alias_default_alias_expression(self):
        qs = Author.objects.alias(
            Sum("book__pages"),
        ).filter(book__pages__sum__gt=2000)
        self.assertIs(hasattr(qs.first(), "book__pages__sum"), False)
        self.assertSequenceEqual(qs, [self.a4])