def test_db_default_literal(self):
        class Model(models.Model):
            field = models.IntegerField(db_default=1)

        field = Model._meta.get_field("field")
        errors = field.check(databases=self.databases)
        self.assertEqual(errors, [])