async def test_properties_async_versions(self):
        self.assertEqual(await self.user.groups.acount(), 0)
        self.assertEqual(await self.user.user_permissions.acount(), 0)
        self.assertEqual(await self.user.aget_user_permissions(), set())
        self.assertEqual(await self.user.aget_group_permissions(), set())