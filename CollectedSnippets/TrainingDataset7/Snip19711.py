def test_raw(self):
        users = User.objects.raw("SELECT * FROM composite_pk_user")
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user.tenant_id, self.user.tenant_id)
        self.assertEqual(user.id, self.user.id)
        self.assertEqual(user.email, self.user.email)