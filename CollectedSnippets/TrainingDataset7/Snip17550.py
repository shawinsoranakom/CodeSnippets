async def test_ahas_perms_perm_list_invalid(self):
        msg = "perm_list must be an iterable of permissions."
        with self.assertRaisesMessage(ValueError, msg):
            await self.user1.ahas_perms("perm")
        with self.assertRaisesMessage(ValueError, msg):
            await self.user1.ahas_perms(object())