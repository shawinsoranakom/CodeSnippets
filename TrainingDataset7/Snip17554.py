async def test_aget_all_permissions(self):
        self.assertEqual(await self.user1.aget_all_permissions(TestObj()), {"anon"})