async def test_acustom_perms(self):
        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        content_type = await sync_to_async(ContentType.objects.get_for_model)(Group)
        perm = await Permission.objects.acreate(
            name="test", content_type=content_type, codename="test"
        )
        await user.user_permissions.aadd(perm)

        # Reloading user to purge the _perm_cache.
        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        self.assertEqual(await user.aget_all_permissions(), {"auth.test"})
        self.assertEqual(await user.aget_user_permissions(), {"auth.test"})
        self.assertEqual(await user.aget_group_permissions(), set())
        self.assertIs(await user.ahas_module_perms("Group"), False)
        self.assertIs(await user.ahas_module_perms("auth"), True)

        perm = await Permission.objects.acreate(
            name="test2", content_type=content_type, codename="test2"
        )
        await user.user_permissions.aadd(perm)
        perm = await Permission.objects.acreate(
            name="test3", content_type=content_type, codename="test3"
        )
        await user.user_permissions.aadd(perm)
        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        expected_user_perms = {"auth.test2", "auth.test", "auth.test3"}
        self.assertEqual(await user.aget_all_permissions(), expected_user_perms)
        self.assertIs(await user.ahas_perm("test"), False)
        self.assertIs(await user.ahas_perm("auth.test"), True)
        self.assertIs(await user.ahas_perms(["auth.test2", "auth.test3"]), True)

        perm = await Permission.objects.acreate(
            name="test_group", content_type=content_type, codename="test_group"
        )
        group = await Group.objects.acreate(name="test_group")
        await group.permissions.aadd(perm)
        await user.groups.aadd(group)
        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        self.assertEqual(
            await user.aget_all_permissions(), {*expected_user_perms, "auth.test_group"}
        )
        self.assertEqual(await user.aget_user_permissions(), expected_user_perms)
        self.assertEqual(await user.aget_group_permissions(), {"auth.test_group"})
        self.assertIs(await user.ahas_perms(["auth.test3", "auth.test_group"]), True)

        user = AnonymousUser()
        self.assertIs(await user.ahas_perm("test"), False)
        self.assertIs(await user.ahas_perms(["auth.test2", "auth.test3"]), False)