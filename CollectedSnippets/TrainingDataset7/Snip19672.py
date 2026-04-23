def test_update_fields_deferred(self):
        c = Comment.objects.defer("text", "user_id").get(pk=self.comment_1.pk)
        c.text = "Hello"

        with self.assertNumQueries(1) as ctx:
            c.save()

        sql = ctx[0]["sql"]
        self.assertEqual(sql.count(connection.ops.quote_name("tenant_id")), 1)
        self.assertEqual(sql.count(connection.ops.quote_name("comment_id")), 1)

        c = Comment.objects.get(pk=self.comment_1.pk)
        self.assertEqual(c.text, "Hello")