def test_annotation_with_outerref(self):
        gmbh_salary = Company.objects.annotate(
            max_ceo_salary_raise=Subquery(
                Company.objects.annotate(
                    salary_raise=OuterRef("num_employees") + F("num_employees"),
                )
                .order_by("-salary_raise")
                .values("salary_raise")[:1],
            ),
        ).get(pk=self.gmbh.pk)
        self.assertEqual(gmbh_salary.max_ceo_salary_raise, 2332)