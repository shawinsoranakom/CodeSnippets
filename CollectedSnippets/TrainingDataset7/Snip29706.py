def test_opclass_partial(self):
        constraint = UniqueConstraint(
            name="test_opclass_partial",
            fields=["scene"],
            opclasses=["varchar_pattern_ops"],
            condition=Q(setting__contains="Sir Bedemir's Castle"),
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Scene, constraint)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [constraint.name])
            self.assertCountEqual(
                cursor.fetchall(),
                [("varchar_pattern_ops", constraint.name)],
            )