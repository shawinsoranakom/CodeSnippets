def test_text_indexes(self):
        """Test creation of PostgreSQL-specific text indexes (#12234)"""
        from .models import IndexedArticle

        index_sql = [
            str(statement)
            for statement in connection.schema_editor()._model_indexes_sql(
                IndexedArticle
            )
        ]
        self.assertEqual(len(index_sql), 5)
        self.assertIn('("headline" varchar_pattern_ops)', index_sql[1])
        self.assertIn('("body" text_pattern_ops)', index_sql[3])
        # unique=True and db_index=True should only create the varchar-specific
        # index (#19441).
        self.assertIn('("slug" varchar_pattern_ops)', index_sql[4])