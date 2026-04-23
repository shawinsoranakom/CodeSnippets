def test_max_length_warning(self):
        class Model(models.Model):
            value = models.TextField(db_index=True)

        field = Model._meta.get_field("value")
        field_type = field.db_type(connection)
        self.assertEqual(
            field.check(databases=self.databases),
            [
                DjangoWarning(
                    "%s does not support a database index on %s columns."
                    % (connection.display_name, field_type),
                    hint=(
                        "An index won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=field,
                    id="fields.W162",
                )
            ],
        )