def test_func_index_f_decimalfield(self):
        class Node(Model):
            value = DecimalField(max_digits=5, decimal_places=2)

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Node)
        index = Index(F("value"), name="func_f_decimalfield_idx")
        # Add index.
        with connection.schema_editor() as editor:
            editor.add_index(Node, index)
            sql = index.create_sql(Node, editor)
        table = Node._meta.db_table
        self.assertIn(index.name, self.get_constraints(table))
        self.assertIs(sql.references_column(table, "value"), True)
        # SQL doesn't contain casting.
        self.assertNotIn("CAST", str(sql))
        # Remove index.
        with connection.schema_editor() as editor:
            editor.remove_index(Node, index)
        self.assertNotIn(index.name, self.get_constraints(table))