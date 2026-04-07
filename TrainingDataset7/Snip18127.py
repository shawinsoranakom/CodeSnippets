async def test_agroup_natural_key(self):
        users_group = await Group.objects.acreate(name="users")
        self.assertEqual(await Group.objects.aget_by_natural_key("users"), users_group)