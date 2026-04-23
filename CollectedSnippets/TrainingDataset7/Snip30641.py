def test_combining_does_not_mutate(self):
        all_authors = Author.objects.all()
        authors_with_report = Author.objects.filter(
            Exists(Report.objects.filter(creator__pk=OuterRef("id")))
        )
        authors_without_report = all_authors.exclude(pk__in=authors_with_report)
        items_before = Item.objects.filter(creator__in=authors_without_report)
        self.assertCountEqual(items_before, [self.i2, self.i3, self.i4])
        # Combining querysets doesn't mutate them.
        all_authors | authors_with_report
        all_authors & authors_with_report

        authors_without_report = all_authors.exclude(pk__in=authors_with_report)
        items_after = Item.objects.filter(creator__in=authors_without_report)

        self.assertCountEqual(items_after, [self.i2, self.i3, self.i4])
        self.assertCountEqual(items_before, items_after)