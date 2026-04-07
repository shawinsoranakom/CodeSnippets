async def test_ahas_perm(self):
        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        self.assertIs(await user.ahas_perm("auth.test"), False)

        user.is_staff = True
        await user.asave()
        self.assertIs(await user.ahas_perm("auth.test"), False)

        user.is_superuser = True
        await user.asave()
        self.assertIs(await user.ahas_perm("auth.test"), True)
        self.assertIs(await user.ahas_module_perms("auth"), True)

        user.is_staff = True
        user.is_superuser = True
        user.is_active = False
        await user.asave()
        self.assertIs(await user.ahas_perm("auth.test"), False)