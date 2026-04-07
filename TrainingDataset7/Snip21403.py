def test_case_in_filter_if_boolean_output_field(self):
        is_ceo = Company.objects.filter(ceo=OuterRef("pk"))
        is_poc = Company.objects.filter(point_of_contact=OuterRef("pk"))
        qs = Employee.objects.filter(
            Case(
                When(Exists(is_ceo), then=True),
                When(Exists(is_poc), then=True),
                default=False,
                output_field=BooleanField(),
            ),
        )
        self.assertCountEqual(qs, [self.example_inc.ceo, self.foobar_ltd.ceo, self.max])