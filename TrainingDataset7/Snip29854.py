def test_tsvector_op_class_gist_index(self):
        index_name = "tsvector_op_class_gist"
        index = GistIndex(
            OpClass(
                SearchVector("scene", "setting", config="english"),
                name="tsvector_ops",
            ),
            name=index_name,
        )
        with connection.schema_editor() as editor:
            editor.add_index(Scene, index)
            sql = index.create_sql(Scene, editor)
        table = Scene._meta.db_table
        constraints = self.get_constraints(table)
        self.assertIn(index_name, constraints)
        self.assertIn(constraints[index_name]["type"], GistIndex.suffix)
        self.assertIs(sql.references_column(table, "scene"), True)
        self.assertIs(sql.references_column(table, "setting"), True)
        with connection.schema_editor() as editor:
            editor.remove_index(Scene, index)
        self.assertNotIn(index_name, self.get_constraints(table))