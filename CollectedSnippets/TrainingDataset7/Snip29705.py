def test_opclass_multiple_columns(self):
        constraint = UniqueConstraint(
            name="test_opclass_multiple",
            fields=["scene", "setting"],
            opclasses=["varchar_pattern_ops", "text_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Scene, constraint)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [constraint.name])
            expected_opclasses = (
                ("varchar_pattern_ops", constraint.name),
                ("text_pattern_ops", constraint.name),
            )
            self.assertCountEqual(cursor.fetchall(), expected_opclasses)