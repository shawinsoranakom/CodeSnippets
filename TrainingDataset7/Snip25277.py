def test_db_comments(self):
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(
                cursor, DbCommentModel._meta.db_table
            )
            table_list = connection.introspection.get_table_list(cursor)
        self.assertEqual(
            ["'Name' column comment"],
            [field.comment for field in desc if field.name == "name"],
        )
        self.assertEqual(
            ["Custom table comment"],
            [
                table.comment
                for table in table_list
                if table.name == "introspection_dbcommentmodel"
            ],
        )