def test_subquery_eq(self):
        qs = Employee.objects.annotate(
            is_ceo=Exists(Company.objects.filter(ceo=OuterRef("pk"))),
            is_point_of_contact=Exists(
                Company.objects.filter(point_of_contact=OuterRef("pk")),
            ),
            small_company=Exists(
                queryset=Company.objects.filter(num_employees__lt=200),
            ),
        ).filter(is_ceo=True, is_point_of_contact=False, small_company=True)
        self.assertNotEqual(
            qs.query.annotations["is_ceo"],
            qs.query.annotations["is_point_of_contact"],
        )
        self.assertNotEqual(
            qs.query.annotations["is_ceo"],
            qs.query.annotations["small_company"],
        )