def test_key_transform(self):
        Detail.objects.bulk_create(
            [
                Detail(value={"department": "IT", "name": "Smith", "salary": 37000}),
                Detail(value={"department": "IT", "name": "Nowak", "salary": 32000}),
                Detail(value={"department": "HR", "name": "Brown", "salary": 50000}),
                Detail(value={"department": "HR", "name": "Smith", "salary": 55000}),
                Detail(value={"department": "PR", "name": "Moore", "salary": 90000}),
            ]
        )
        tests = [
            (KeyTransform("department", "value"), KeyTransform("name", "value")),
            (F("value__department"), F("value__name")),
        ]
        for partition_by, order_by in tests:
            with self.subTest(partition_by=partition_by, order_by=order_by):
                qs = Detail.objects.annotate(
                    department_sum=Window(
                        expression=Sum(
                            Cast(
                                KeyTextTransform("salary", "value"),
                                output_field=IntegerField(),
                            )
                        ),
                        partition_by=[partition_by],
                        order_by=[order_by],
                    )
                ).order_by("value__department", "department_sum")
                self.assertQuerySetEqual(
                    qs,
                    [
                        ("Brown", "HR", 50000, 50000),
                        ("Smith", "HR", 55000, 105000),
                        ("Nowak", "IT", 32000, 32000),
                        ("Smith", "IT", 37000, 69000),
                        ("Moore", "PR", 90000, 90000),
                    ],
                    lambda entry: (
                        entry.value["name"],
                        entry.value["department"],
                        entry.value["salary"],
                        entry.department_sum,
                    ),
                )