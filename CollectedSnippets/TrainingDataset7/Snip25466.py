def test_too_long_char_field_under_mysql(self):
        from django.db.backends.mysql.validation import DatabaseValidation

        class Model(models.Model):
            field = models.CharField(unique=True, max_length=256)

        field = Model._meta.get_field("field")
        validator = DatabaseValidation(connection=connection)
        self.assertEqual(
            validator.check_field(field),
            [
                DjangoWarning(
                    "%s may not allow unique CharFields to have a max_length > "
                    "255." % connection.display_name,
                    hint=(
                        "See: https://docs.djangoproject.com/en/%s/ref/databases/"
                        "#mysql-character-fields" % get_docs_version()
                    ),
                    obj=field,
                    id="mysql.W003",
                )
            ],
        )