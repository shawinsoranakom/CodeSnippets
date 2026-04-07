async def test_ahas_no_object_perm(self):
        """See test_has_no_object_perm()"""
        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        content_type = await sync_to_async(ContentType.objects.get_for_model)(Group)
        perm = await Permission.objects.acreate(
            name="test", content_type=content_type, codename="test"
        )
        await user.user_permissions.aadd(perm)

        self.assertIs(await user.ahas_perm("auth.test", "object"), False)
        self.assertEqual(await user.aget_all_permissions("object"), set())
        self.assertIs(await user.ahas_perm("auth.test"), True)
        self.assertEqual(await user.aget_all_permissions(), {"auth.test"})