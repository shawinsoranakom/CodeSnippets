def test_execute_sql_flush_statements(self):
        with transaction.atomic():
            author = Author.objects.create(name="George Orwell")
            Book.objects.create(author=author)
            author = Author.objects.create(name="Harper Lee")
            Book.objects.create(author=author)
            Book.objects.create(author=author)
            self.assertIs(Author.objects.exists(), True)
            self.assertIs(Book.objects.exists(), True)

        sql_list = connection.ops.sql_flush(
            no_style(),
            [Author._meta.db_table, Book._meta.db_table],
            reset_sequences=True,
            allow_cascade=True,
        )
        connection.ops.execute_sql_flush(sql_list)

        with transaction.atomic():
            self.assertIs(Author.objects.exists(), False)
            self.assertIs(Book.objects.exists(), False)
            if connection.features.supports_sequence_reset:
                author = Author.objects.create(name="F. Scott Fitzgerald")
                self.assertEqual(author.pk, 1)
                book = Book.objects.create(author=author)
                self.assertEqual(book.pk, 1)