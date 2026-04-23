async def test_get_list_or_404_bad_class(self):
        msg = (
            "First argument to aget_list_or_404() must be a Model, Manager, or "
            "QuerySet, not 'list'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            await aget_list_or_404([SimpleModel], field=1)