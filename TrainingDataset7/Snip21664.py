def test_related_ordering_with_count(self):
        qs = Employee.objects.annotate(
            department_sum=Window(
                expression=Sum("salary"),
                partition_by=F("department"),
                order_by=["classification__code"],
            )
        )
        self.assertEqual(qs.count(), 12)