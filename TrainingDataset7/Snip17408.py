async def test_update_conflicts_unique_field_unsupported(self):
        msg = (
            "This database backend does not support updating conflicts with specifying "
            "unique fields that can trigger the upsert."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            await SimpleModel.objects.abulk_create(
                [SimpleModel(field=1), SimpleModel(field=2)],
                update_conflicts=True,
                update_fields=["field"],
                unique_fields=["created"],
            )