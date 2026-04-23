async def test_acount_cached_result(self):
        qs = SimpleModel.objects.all()
        # Evaluate the queryset to populate the query cache.
        [x async for x in qs]
        count = await qs.acount()
        self.assertEqual(count, 3)

        await sync_to_async(SimpleModel.objects.create)(
            field=4,
            created=datetime(2022, 1, 1, 0, 0, 0),
        )
        # The query cache is used.
        count = await qs.acount()
        self.assertEqual(count, 3)