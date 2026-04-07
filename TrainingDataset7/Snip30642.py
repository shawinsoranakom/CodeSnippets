def test_union_values_subquery(self):
        items = Item.objects.filter(creator=OuterRef("pk"))
        item_authors = Author.objects.annotate(is_creator=Exists(items)).order_by()
        reports = Report.objects.filter(creator=OuterRef("pk"))
        report_authors = Author.objects.annotate(is_creator=Exists(reports)).order_by()
        all_authors = item_authors.union(report_authors).order_by("is_creator")
        self.assertEqual(
            list(all_authors.values_list("is_creator", flat=True)), [False, True]
        )