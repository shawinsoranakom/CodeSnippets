def test_bad_db_index_value(self):
        class Model(models.Model):
            field = models.CharField(max_length=10, db_index="bad")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'db_index' must be None, True or False.",
                    obj=field,
                    id="fields.E006",
                ),
            ],
        )