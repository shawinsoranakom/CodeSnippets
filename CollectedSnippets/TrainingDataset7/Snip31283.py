def test_add_inline_fk_index_update_data(self):
        class Node(Model):
            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Node)
        # Add an inline foreign key, update data, and an index in the same
        # transaction.
        new_field = ForeignKey(Node, CASCADE, related_name="new_fk", null=True)
        new_field.set_attributes_from_name("new_parent_fk")
        parent = Node.objects.create()
        with connection.schema_editor() as editor:
            editor.add_field(Node, new_field)
            Node._meta.add_field(new_field)
            editor.execute("UPDATE schema_node SET new_parent_fk_id = %s;", [parent.pk])
            editor.add_index(
                Node, Index(fields=["new_parent_fk"], name="new_parent_inline_fk_idx")
            )
        self.assertIn("new_parent_fk_id", self.get_indexes(Node._meta.db_table))