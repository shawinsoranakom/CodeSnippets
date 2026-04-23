def test_alter_fk_checks_deferred_constraints(self):
        """
        #25492 - Altering a foreign key's structure and data in the same
        transaction.
        """
        with connection.schema_editor() as editor:
            editor.create_model(Node)
        old_field = Node._meta.get_field("parent")
        new_field = ForeignKey(Node, CASCADE)
        new_field.set_attributes_from_name("parent")
        parent = Node.objects.create()
        with connection.schema_editor() as editor:
            # Update the parent FK to create a deferred constraint check.
            Node.objects.update(parent=parent)
            editor.alter_field(Node, old_field, new_field, strict=True)