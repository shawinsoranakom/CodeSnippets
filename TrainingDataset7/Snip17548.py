async def test_ahas_perms(self):
        self.assertIs(await self.user1.ahas_perms(["anon"], TestObj()), True)
        self.assertIs(await self.user1.ahas_perms(["anon", "perm"], TestObj()), False)