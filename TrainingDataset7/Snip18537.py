def test_prepare_join_on_clause(self):
        author_table = Author._meta.db_table
        author_id_field = Author._meta.get_field("id")
        book_table = Book._meta.db_table
        book_fk_field = Book._meta.get_field("author")
        lhs_expr, rhs_expr = self.ops.prepare_join_on_clause(
            author_table,
            author_id_field,
            book_table,
            book_fk_field,
        )
        self.assertEqual(lhs_expr, Col(author_table, author_id_field))
        self.assertEqual(rhs_expr, Col(book_table, book_fk_field))