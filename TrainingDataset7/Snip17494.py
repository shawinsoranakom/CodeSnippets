async def test_aget_user_permissions(self):
        self.assertEqual(await self.user.aget_user_permissions(), {"user_perm"})