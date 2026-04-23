def test_only(self):
        users = User.objects.only("pk")
        self.assertSequenceEqual(users, (self.user,))
        user = users[0]

        with self.assertNumQueries(0):
            self.assertEqual(user.pk, (self.user.tenant_id, self.user.id))
            self.assertEqual(user.tenant_id, self.user.tenant_id)
            self.assertEqual(user.id, self.user.id)
        with self.assertNumQueries(1):
            self.assertEqual(user.email, self.user.email)