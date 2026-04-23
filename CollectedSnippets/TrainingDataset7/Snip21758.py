def test_many_to_many_field_related_name(self):
        class MyModel(models.Model):
            flag = models.BooleanField(default=True)
            m2m = models.ManyToManyField("self")
            m2m_related_name = models.ManyToManyField(
                "self",
                related_query_name="custom_query_name",
                limit_choices_to={"flag": True},
            )

        name, path, args, kwargs = MyModel.m2m.field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        # deconstruct() should not include attributes which were not passed to
        # the field during initialization.
        self.assertEqual(kwargs, {"to": "field_deconstruction.mymodel"})
        # Passed attributes.
        name, path, args, kwargs = MyModel.m2m_related_name.field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "to": "field_deconstruction.mymodel",
                "related_query_name": "custom_query_name",
                "limit_choices_to": {"flag": True},
            },
        )