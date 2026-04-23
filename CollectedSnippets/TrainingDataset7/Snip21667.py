def test_filter_conditional_expression(self):
        qs = (
            Employee.objects.filter(
                Exact(Window(Rank(), partition_by="department", order_by="-salary"), 1)
            )
            .order_by("name")
            .values_list("name", flat=True)
        )
        self.assertSequenceEqual(
            qs, ["Adams", "Johnson", "Miller", "Smith", "Wilkinson"]
        )