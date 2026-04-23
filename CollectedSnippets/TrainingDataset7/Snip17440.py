async def test_get_object_or_404_bad_class(self):
        msg = (
            "First argument to aget_object_or_404() must be a Model, Manager, or "
            "QuerySet, not 'str'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            await aget_object_or_404("SimpleModel", field=0)