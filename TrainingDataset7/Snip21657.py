def test_lead_default(self):
        qs = Employee.objects.annotate(
            lead_default=Window(
                expression=Lead(expression="salary", offset=5, default=60000),
                partition_by=F("department"),
                order_by=F("department").asc(),
            )
        )
        self.assertEqual(
            list(qs.values_list("lead_default", flat=True).distinct()), [60000]
        )