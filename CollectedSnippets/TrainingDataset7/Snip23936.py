def test_update_only_defaults_and_pre_save_fields_when_local_fields(self):
        publisher = Publisher.objects.create(name="Acme Publishing")
        book = Book.objects.create(publisher=publisher, name="The Book of Ed & Fred")

        for defaults in [{"publisher": publisher}, {"publisher_id": publisher}]:
            with self.subTest(defaults=defaults):
                with CaptureQueriesContext(connection) as captured_queries:
                    book, created = Book.objects.update_or_create(
                        pk=book.pk,
                        defaults=defaults,
                    )
                self.assertIs(created, False)
                update_sqls = [
                    q["sql"] for q in captured_queries if q["sql"].startswith("UPDATE")
                ]
                self.assertEqual(len(update_sqls), 1)
                update_sql = update_sqls[0]
                self.assertIsNotNone(update_sql)
                self.assertIn(
                    connection.ops.quote_name("publisher_id_column"), update_sql
                )
                self.assertIn(connection.ops.quote_name("updated"), update_sql)
                # Name should not be updated.
                self.assertNotIn(connection.ops.quote_name("name"), update_sql)