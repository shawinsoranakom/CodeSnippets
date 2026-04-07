def test_user_natural_key(self):
        staff_user = User.objects.create_user(username="staff")
        self.assertEqual(User.objects.get_by_natural_key("staff"), staff_user)
        self.assertEqual(staff_user.natural_key(), ("staff",))