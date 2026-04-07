def test_max_length_warning(self):
        class Model(models.Model):
            auto = models.AutoField(primary_key=True, max_length=2)

        field = Model._meta.get_field("auto")
        self.assertEqual(
            field.check(),
            [
                DjangoWarning(
                    "'max_length' is ignored when used with %s."
                    % field.__class__.__name__,
                    hint="Remove 'max_length' from field",
                    obj=field,
                    id="fields.W122",
                ),
            ],
        )