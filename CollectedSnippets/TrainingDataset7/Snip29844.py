def test_cast_search_vector_gin_index(self):
        index_name = "cast_search_vector_gin"
        index = GinIndex(Cast("field", SearchVectorField()), name=index_name)
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
            sql = index.create_sql(TextFieldModel, editor)
        table = TextFieldModel._meta.db_table
        constraints = self.get_constraints(table)
        self.assertIn(index_name, constraints)
        self.assertIn(constraints[index_name]["type"], GinIndex.suffix)
        self.assertIs(sql.references_column(table, "field"), True)
        self.assertIn("::tsvector", str(sql))
        with connection.schema_editor() as editor:
            editor.remove_index(TextFieldModel, index)
        self.assertNotIn(index_name, self.get_constraints(table))