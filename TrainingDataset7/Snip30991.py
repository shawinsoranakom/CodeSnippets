def test_db_column_name_is_used_in_raw_query(self):
        """
        Regression test that ensures the `column` attribute on the field is
        used to generate the list of fields included in the query, as opposed
        to the `attname`. This is important when the primary key is a
        ForeignKey field because `attname` and `column` are not necessarily the
        same.
        """
        b = BookFkAsPk.objects.create(book=self.b1)
        self.assertEqual(
            list(
                BookFkAsPk.objects.raw(
                    "SELECT not_the_default FROM raw_query_bookfkaspk"
                )
            ),
            [b],
        )