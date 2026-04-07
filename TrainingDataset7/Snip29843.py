def test_trigram_op_class_gin_index(self):
        index_name = "trigram_op_class_gin"
        index = GinIndex(OpClass(F("scene"), name="gin_trgm_ops"), name=index_name)
        with connection.schema_editor() as editor:
            editor.add_index(Scene, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [index_name])
            self.assertCountEqual(cursor.fetchall(), [("gin_trgm_ops", index_name)])
        constraints = self.get_constraints(Scene._meta.db_table)
        self.assertIn(index_name, constraints)
        self.assertIn(constraints[index_name]["type"], GinIndex.suffix)
        with connection.schema_editor() as editor:
            editor.remove_index(Scene, index)
        self.assertNotIn(index_name, self.get_constraints(Scene._meta.db_table))