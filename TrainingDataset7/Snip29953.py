def test_choices_tuple_list(self):
        class Model(PostgreSQLModel):
            field = pg_fields.IntegerRangeField(
                choices=[
                    ["1-50", [((1, 25), "1-25"), ([26, 50], "26-50")]],
                    ((51, 100), "51-100"),
                ],
            )

        self.assertEqual(Model._meta.get_field("field").check(), [])