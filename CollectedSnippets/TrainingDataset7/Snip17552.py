async def test_ahas_module_perms(self):
        self.assertIs(await self.user1.ahas_module_perms("app1"), True)
        self.assertIs(await self.user1.ahas_module_perms("app2"), False)