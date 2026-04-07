async def test_arefresh_from_db_from_queryset(self):
        await SimpleModel.objects.filter(pk=self.s1.pk).aupdate(field=20)
        with self.assertRaises(SimpleModel.DoesNotExist):
            await self.s1.arefresh_from_db(
                from_queryset=SimpleModel.objects.filter(field=0)
            )
        await self.s1.arefresh_from_db(
            from_queryset=SimpleModel.objects.filter(field__gt=0)
        )
        self.assertEqual(self.s1.field, 20)