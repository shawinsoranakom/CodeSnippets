async def test_aget_all_permissions(self):
        self.assertEqual(
            await self.user.aget_all_permissions(), {"user_perm", "group_perm"}
        )