def test_in_bulk_batching(self):
        Comment.objects.all().delete()
        num_objects = 10
        connection.features.__dict__.pop("max_query_params", None)
        with unittest.mock.patch.object(
            type(connection.features), "max_query_params", num_objects
        ):
            comments = [
                Comment(id=i, tenant=self.tenant, user=self.user)
                for i in range(1, num_objects + 1)
            ]
            Comment.objects.bulk_create(comments)
            id_list = list(Comment.objects.values_list("pk", flat=True))
            with self.assertNumQueries(2):
                comment_dict = Comment.objects.in_bulk(id_list=id_list)
        self.assertQuerySetEqual(comment_dict, id_list)