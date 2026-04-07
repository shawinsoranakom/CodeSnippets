def test_column_field_ordering_with_deferred(self):
        store = Store.objects.first()
        Employee.objects.create(
            id=1,
            first_name="Max",
            manager=True,
            last_name="Paine",
            store=store,
            age=23,
            salary=Decimal(50000.00),
        )
        Employee.objects.create(
            id=2,
            first_name="Buffy",
            manager=False,
            last_name="Summers",
            store=store,
            age=18,
            salary=Decimal(40000.00),
        )

        qs = (
            Employee.objects.extra(select={"random_value": "42"})
            .select_related("store")
            .annotate(
                annotated_value=Value(17),
            )
        )

        rows = [
            (1, "Max", True, 42, "Paine", 23, Decimal(50000.00), store.name, 17),
            (2, "Buffy", False, 42, "Summers", 18, Decimal(40000.00), store.name, 17),
        ]

        # and we respect deferred columns!
        self.assertQuerySetEqual(
            qs.defer("age").order_by("id"),
            rows,
            lambda e: (
                e.id,
                e.first_name,
                e.manager,
                e.random_value,
                e.last_name,
                e.age,
                e.salary,
                e.store.name,
                e.annotated_value,
            ),
        )