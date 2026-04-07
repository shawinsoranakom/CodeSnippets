def test_default_iterator_chunk_size(self):
        qs = Article.objects.iterator()
        with mock.patch(
            "django.db.models.sql.compiler.cursor_iter", side_effect=cursor_iter
        ) as cursor_iter_mock:
            next(qs)
        self.assertEqual(cursor_iter_mock.call_count, 1)
        mock_args, _mock_kwargs = cursor_iter_mock.call_args
        self.assertEqual(mock_args[self.itersize_index_in_mock_args], 2000)