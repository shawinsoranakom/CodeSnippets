def test_get_constraints_index_types(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, Article._meta.db_table
            )
        index = {}
        index2 = {}
        for val in constraints.values():
            if val["columns"] == ["headline", "pub_date"]:
                index = val
            if val["columns"] == [
                "headline",
                "response_to_id",
                "pub_date",
                "reporter_id",
            ]:
                index2 = val
        self.assertEqual(index["type"], Index.suffix)
        self.assertEqual(index2["type"], Index.suffix)