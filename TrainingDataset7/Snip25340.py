def test_db_column_clash(self):
        class Model(models.Model):
            foo = models.IntegerField()
            bar = models.IntegerField(db_column="foo")

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Field 'bar' has column name 'foo' that is used by "
                    "another field.",
                    hint="Specify a 'db_column' for the field.",
                    obj=Model,
                    id="models.E007",
                )
            ],
        )