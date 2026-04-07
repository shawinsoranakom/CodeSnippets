def test_save_user(self):
        count = User.objects.count()
        email = "user9314@example.com"
        user = User.objects.get(pk=self.user_1.pk)
        user.email = email
        with self.assertNumQueries(1) as ctx:
            user.save()
        sql = ctx[0]["sql"]
        self.assertEqual(sql.count(connection.ops.quote_name("tenant_id")), 1)
        self.assertEqual(sql.count(connection.ops.quote_name("id")), 1)
        user.refresh_from_db()
        self.assertEqual(user.email, email)
        user = User.objects.get(pk=self.user_1.pk)
        self.assertEqual(user.email, email)
        self.assertEqual(count, User.objects.count())