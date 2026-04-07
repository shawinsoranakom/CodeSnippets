def test_update_conflicts_nonexistent_update_fields(self):
        unique_fields = None
        if connection.features.supports_update_conflicts_with_target:
            unique_fields = ["f1"]
        msg = "TwoFields has no field named 'nonexistent'"
        with self.assertRaisesMessage(FieldDoesNotExist, msg):
            TwoFields.objects.bulk_create(
                [TwoFields(f1=1, f2=1), TwoFields(f1=2, f2=2)],
                update_conflicts=True,
                update_fields=["nonexistent"],
                unique_fields=unique_fields,
            )