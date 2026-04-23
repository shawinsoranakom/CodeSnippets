def test_subquery_group_by_outerref_in_filter(self):
        inner = (
            Company.objects.annotate(
                employee=OuterRef("pk"),
            )
            .values("employee")
            .annotate(
                min_num_chairs=Min("num_chairs"),
            )
            .values("ceo")
        )
        self.assertIs(Employee.objects.filter(pk__in=Subquery(inner)).exists(), True)