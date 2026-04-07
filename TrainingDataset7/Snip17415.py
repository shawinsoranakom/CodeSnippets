async def test_aaggregate(self):
        total = await SimpleModel.objects.aaggregate(total=Sum("field"))
        self.assertEqual(total, {"total": 6})