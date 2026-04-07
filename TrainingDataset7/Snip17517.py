async def test_aget_all_superuser_permissions(self):
        """See test_get_all_superuser_permissions()"""
        user = await self.UserModel._default_manager.aget(pk=self.superuser.pk)
        self.assertEqual(
            len(await user.aget_all_permissions()), await Permission.objects.acount()
        )