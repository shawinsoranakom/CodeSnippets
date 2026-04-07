def test_update_conflicts_unique_field_unsupported(self):
        msg = (
            "This database backend does not support updating conflicts with "
            "specifying unique fields that can trigger the upsert."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            TwoFields.objects.bulk_create(
                [TwoFields(f1=1, f2=1), TwoFields(f1=2, f2=2)],
                update_conflicts=True,
                update_fields=["f2"],
                unique_fields=["f1"],
            )