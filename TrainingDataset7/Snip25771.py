def test_in_bulk_preserve_ordering_with_batch_size(self):
        qs = Article.objects.all()
        with (
            mock.patch.object(connection.ops, "bulk_batch_size", return_value=2),
            self.assertNumQueries(2),
        ):
            self.assertEqual(
                list(qs.in_bulk([self.a4.id, self.a3.id, self.a2.id, self.a1.id])),
                [self.a4.id, self.a3.id, self.a2.id, self.a1.id],
            )