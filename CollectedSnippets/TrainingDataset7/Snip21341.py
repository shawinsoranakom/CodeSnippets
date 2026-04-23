def test_slicing_of_f_expression_with_annotated_expression(self):
        qs = Company.objects.annotate(
            new_name=Case(
                When(based_in_eu=True, then=Concat(Value("EU:"), F("name"))),
                default=F("name"),
            ),
            first_two=F("new_name")[:3],
        )
        self.assertCountEqual(
            qs.values_list("first_two", flat=True),
            ["Exa", "EU:", "Tes"],
        )