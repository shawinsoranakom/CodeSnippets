def test_select_related(self):
        Comment.objects.create(tenant=self.tenant, id=2)
        with self.assertNumQueries(1):
            comments = list(Comment.objects.select_related("user").order_by("pk"))
            self.assertEqual(len(comments), 2)
            self.assertEqual(comments[0].user, self.user)
            self.assertIsNone(comments[1].user)