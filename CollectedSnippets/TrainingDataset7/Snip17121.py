def test_f_expression_annotation(self):
        # Books with less than 200 pages per author.
        qs = (
            Book.objects.values("name")
            .annotate(n_authors=Count("authors"))
            .filter(pages__lt=F("n_authors") * 200)
            .values_list("pk")
        )
        self.assertQuerySetEqual(
            Book.objects.filter(pk__in=qs),
            ["Python Web Development with Django"],
            attrgetter("name"),
        )