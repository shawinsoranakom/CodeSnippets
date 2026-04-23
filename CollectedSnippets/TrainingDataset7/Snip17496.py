async def test_aget_group_permissions(self):
        self.assertEqual(await self.user.aget_group_permissions(), {"group_perm"})