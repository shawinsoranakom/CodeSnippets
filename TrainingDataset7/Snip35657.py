def test_order_by_update_on_unique_constraint_annotation_desc(self):
        updated = (
            UniqueNumber.objects.annotate(number_annotation=F("number"))
            .order_by("-number_annotation")
            .update(number=F("number") + 1)
        )
        self.assertEqual(updated, 2)