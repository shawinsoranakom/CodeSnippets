def test_order_by_update_on_unique_constraint_annotation(self):
        updated = (
            UniqueNumber.objects.annotate(number_inverse=F("number").desc())
            .order_by("number_inverse")
            .update(number=F("number") + 1)
        )
        self.assertEqual(updated, 2)