def test_proxy_update(self):
        user = User.objects.create(name="Bruce")
        with self.assertNumQueries(1):
            UserProxy.objects.filter(id=user.id).update(name="George")
        user.refresh_from_db()
        self.assertEqual(user.name, "George")