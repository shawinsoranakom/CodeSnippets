def test_many_to_many_with_useless_options(self):
        class Model(models.Model):
            name = models.CharField(max_length=20)

        class ModelM2M(models.Model):
            m2m = models.ManyToManyField(
                Model, null=True, validators=[lambda x: x], db_comment="Column comment"
            )

        field = ModelM2M._meta.get_field("m2m")
        self.assertEqual(
            ModelM2M.check(),
            [
                DjangoWarning(
                    "null has no effect on ManyToManyField.",
                    obj=field,
                    id="fields.W340",
                ),
                DjangoWarning(
                    "ManyToManyField does not support validators.",
                    obj=field,
                    id="fields.W341",
                ),
                DjangoWarning(
                    "db_comment has no effect on ManyToManyField.",
                    obj=field,
                    id="fields.W346",
                ),
            ],
        )