def test_nested_subquery(self):
        inner = Company.objects.filter(point_of_contact=OuterRef("pk"))
        outer = Employee.objects.annotate(is_point_of_contact=Exists(inner))
        contrived = Employee.objects.annotate(
            is_point_of_contact=Subquery(
                outer.filter(pk=OuterRef("pk")).values("is_point_of_contact"),
                output_field=BooleanField(),
            ),
        )
        self.assertCountEqual(contrived.values_list(), outer.values_list())