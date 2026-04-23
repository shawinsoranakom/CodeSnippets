def test_content_type_field_pointing_to_wrong_model(self):
        class Model(models.Model):
            content_type = models.ForeignKey(
                "self", models.CASCADE
            )  # should point to ContentType
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey("content_type", "object_id")

        field = Model._meta.get_field("content_object")

        self.assertEqual(
            field.check(),
            [
                checks.Error(
                    "'Model.content_type' is not a ForeignKey to "
                    "'contenttypes.ContentType'.",
                    hint=(
                        "GenericForeignKeys must use a ForeignKey to "
                        "'contenttypes.ContentType' as the 'content_type' field."
                    ),
                    obj=field,
                    id="contenttypes.E004",
                )
            ],
        )