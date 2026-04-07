async def test_ahas_perm(self):
        self.assertIs(await self.user.ahas_perm("user_perm"), True)
        self.assertIs(await self.user.ahas_perm("group_perm"), True)
        self.assertIs(await self.user.ahas_perm("other_perm", TestObj()), False)