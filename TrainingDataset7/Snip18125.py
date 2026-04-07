async def test_auser_natural_key(self):
        staff_user = await User.objects.acreate_user(username="staff")
        self.assertEqual(await User.objects.aget_by_natural_key("staff"), staff_user)
        self.assertEqual(staff_user.natural_key(), ("staff",))