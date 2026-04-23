async def test_ahas_perm_denied(self):
        content_type = await sync_to_async(ContentType.objects.get_for_model)(Group)
        perm = await Permission.objects.acreate(
            name="test", content_type=content_type, codename="test"
        )
        await self.user1.user_permissions.aadd(perm)

        self.assertIs(await self.user1.ahas_perm("auth.test"), False)
        self.assertIs(await self.user1.ahas_module_perms("auth"), False)