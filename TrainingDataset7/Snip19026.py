def test_update_conflicts_invalid_unique_fields(self):
        msg = "bulk_create() can only be used with concrete fields in unique_fields."
        # Reverse one-to-one relationship.
        with self.assertRaisesMessage(ValueError, msg):
            Country.objects.bulk_create(
                self.data,
                update_conflicts=True,
                update_fields=["name"],
                unique_fields=["relatedmodel"],
            )
        # Many-to-many relationship.
        with self.assertRaisesMessage(ValueError, msg):
            RelatedModel.objects.bulk_create(
                [RelatedModel(country=self.data[0])],
                update_conflicts=True,
                update_fields=["name"],
                unique_fields=["big_auto_fields"],
            )