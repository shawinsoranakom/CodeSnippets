async def test_ahas_perm(self):
        self.assertIs(await self.user1.ahas_perm("perm", TestObj()), False)
        self.assertIs(await self.user1.ahas_perm("anon", TestObj()), True)