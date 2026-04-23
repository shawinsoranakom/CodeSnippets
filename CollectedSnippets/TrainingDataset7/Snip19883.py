def test_field_name_ending_with_underscore(self):
        class Model(models.Model):
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object_ = GenericForeignKey("content_type", "object_id")

        field = Model._meta.get_field("content_object_")

        self.assertEqual(
            field.check(),
            [
                checks.Error(
                    "Field names must not end with an underscore.",
                    obj=field,
                    id="fields.E001",
                )
            ],
        )