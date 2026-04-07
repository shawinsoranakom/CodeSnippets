def test_subquery_filter_by_aggregate(self):
        Number.objects.create(integer=1000, float=1.2)
        Employee.objects.create(salary=1000)
        qs = Number.objects.annotate(
            min_valuable_count=Subquery(
                Employee.objects.filter(
                    salary=OuterRef("integer"),
                )
                .annotate(cnt=Count("salary"))
                .filter(cnt__gt=0)
                .values("cnt")[:1]
            ),
        )
        self.assertEqual(qs.get().float, 1.2)