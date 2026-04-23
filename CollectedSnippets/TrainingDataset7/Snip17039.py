def test_group_by_reference_subquery(self):
        author_qs = (
            Author.objects.annotate(publisher_id=F("book__publisher"))
            .values("publisher_id")
            .annotate(cnt=Count("*"))
            .values("publisher_id")
        )
        qs = Publisher.objects.filter(pk__in=author_qs)
        self.assertCountEqual(qs, [self.p1, self.p2, self.p3, self.p4])