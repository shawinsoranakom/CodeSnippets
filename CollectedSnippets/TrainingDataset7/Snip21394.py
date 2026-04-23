def test_annotation_with_outerref_and_output_field(self):
        gmbh_salary = Company.objects.annotate(
            max_ceo_salary_raise=Subquery(
                Company.objects.annotate(
                    salary_raise=OuterRef("num_employees") + F("num_employees"),
                )
                .order_by("-salary_raise")
                .values("salary_raise")[:1],
                output_field=DecimalField(),
            ),
        ).get(pk=self.gmbh.pk)
        self.assertEqual(gmbh_salary.max_ceo_salary_raise, 2332.0)
        self.assertIsInstance(gmbh_salary.max_ceo_salary_raise, Decimal)