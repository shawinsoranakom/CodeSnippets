def test_many_to_many_with_useless_related_name(self):
        class ModelM2M(models.Model):
            m2m = models.ManyToManyField("self", related_name="children")

        field = ModelM2M._meta.get_field("m2m")
        self.assertEqual(
            ModelM2M.check(),
            [
                DjangoWarning(
                    "related_name has no effect on ManyToManyField with "
                    'a symmetrical relationship, e.g. to "self".',
                    obj=field,
                    id="fields.W345",
                ),
            ],
        )