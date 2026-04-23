def test_object_create_with_f_expression_in_subquery(self):
        Company.objects.create(
            name="Big company", num_employees=100000, num_chairs=1, ceo=self.max
        )
        biggest_company = Company.objects.create(
            name="Biggest company",
            num_chairs=1,
            ceo=self.max,
            num_employees=Subquery(
                Company.objects.order_by("-num_employees")
                .annotate(max_num_employees=Max("num_employees"))
                .annotate(new_num_employees=F("max_num_employees") + 1)
                .values("new_num_employees")[:1]
            ),
        )
        biggest_company.refresh_from_db()
        self.assertEqual(biggest_company.num_employees, 100001)