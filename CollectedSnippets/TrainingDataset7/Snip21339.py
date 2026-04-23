def test_slicing_of_f_expressions_textfield(self):
        Text.objects.bulk_create(
            [Text(name=company.name) for company in Company.objects.all()]
        )
        self._test_slicing_of_f_expressions(Text)