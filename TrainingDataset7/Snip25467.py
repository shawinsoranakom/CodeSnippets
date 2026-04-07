def test_db_collation(self):
        class Model(models.Model):
            field = models.CharField(max_length=100, db_collation="anything")

        field = Model._meta.get_field("field")
        error = Error(
            "%s does not support a database collation on CharFields."
            % connection.display_name,
            id="fields.E190",
            obj=field,
        )
        expected = (
            [] if connection.features.supports_collation_on_charfield else [error]
        )
        self.assertEqual(field.check(databases=self.databases), expected)