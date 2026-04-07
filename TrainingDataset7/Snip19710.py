def test_query(self):
        users = User.objects.values_list("pk").order_by("pk")
        self.assertNotIn('AS "pk"', str(users.query))