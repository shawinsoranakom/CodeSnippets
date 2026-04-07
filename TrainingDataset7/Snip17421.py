async def test_raw(self):
        sql = "SELECT id, field FROM async_simplemodel WHERE created=%s"
        qs = SimpleModel.objects.raw(sql, [self.s1.created])
        self.assertEqual([o async for o in qs], [self.s1])