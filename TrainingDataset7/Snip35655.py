def test_order_by_update_on_unique_constraint(self):
        tests = [
            ("-number", "id"),
            (F("number").desc(), "id"),
            (F("number") * -1, "id"),
        ]
        for ordering in tests:
            with self.subTest(ordering=ordering), transaction.atomic():
                updated = UniqueNumber.objects.order_by(*ordering).update(
                    number=F("number") + 1,
                )
                self.assertEqual(updated, 2)