async def test_ainactive_has_no_permissions(self):
        """See test_inactive_has_no_permissions()"""
        backend = ModelBackend()

        user = await self.UserModel._default_manager.aget(pk=self.user.pk)
        content_type = await sync_to_async(ContentType.objects.get_for_model)(Group)
        user_perm = await Permission.objects.acreate(
            name="test", content_type=content_type, codename="test_user"
        )
        group_perm = await Permission.objects.acreate(
            name="test2", content_type=content_type, codename="test_group"
        )
        await user.user_permissions.aadd(user_perm)

        group = await Group.objects.acreate(name="test_group")
        await user.groups.aadd(group)
        await group.permissions.aadd(group_perm)

        self.assertEqual(
            await backend.aget_all_permissions(user),
            {"auth.test_user", "auth.test_group"},
        )
        self.assertEqual(await backend.aget_user_permissions(user), {"auth.test_user"})
        self.assertEqual(
            await backend.aget_group_permissions(user), {"auth.test_group"}
        )

        user.is_active = False
        await user.asave()

        self.assertEqual(await backend.aget_all_permissions(user), set())
        self.assertEqual(await backend.aget_user_permissions(user), set())
        self.assertEqual(await backend.aget_group_permissions(user), set())