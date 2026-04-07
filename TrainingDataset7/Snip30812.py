def test_exclude_subquery(self):
        subquery = JobResponsibilities.objects.filter(
            responsibility__description="bar",
        ) | JobResponsibilities.objects.exclude(
            job__responsibilities__description="foo",
        )
        self.assertCountEqual(
            Job.objects.annotate(
                responsibility=subquery.filter(job=OuterRef("name")).values("id")[:1]
            ),
            [self.j1, self.j2],
        )