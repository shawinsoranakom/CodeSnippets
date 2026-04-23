def test_annotate_values_aggregate(self):
        companies = (
            Company.objects.annotate(
                salaries=F("ceo__salary"),
            )
            .values("num_employees", "salaries")
            .aggregate(
                result=Sum(
                    F("salaries") + F("num_employees"), output_field=IntegerField()
                ),
            )
        )
        self.assertEqual(companies["result"], 2395)