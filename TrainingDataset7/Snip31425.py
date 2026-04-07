def test_func_unique_constraint_nonexistent_field(self):
        constraint = UniqueConstraint(Lower("nonexistent"), name="func_nonexistent_uq")
        msg = (
            "Cannot resolve keyword 'nonexistent' into field. Choices are: "
            "height, id, name, uuid, weight"
        )
        with self.assertRaisesMessage(FieldError, msg):
            with connection.schema_editor() as editor:
                editor.add_constraint(Author, constraint)