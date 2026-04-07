def test_update_conflicts_pk_in_update_fields(self):
        msg = "bulk_create() cannot be used with primary keys in update_fields."
        with self.assertRaisesMessage(ValueError, msg):
            BigAutoFieldModel.objects.bulk_create(
                [BigAutoFieldModel()],
                update_conflicts=True,
                update_fields=["id"],
                unique_fields=["id"],
            )