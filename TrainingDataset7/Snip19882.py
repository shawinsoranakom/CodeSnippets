def test_missing_object_id_field(self):
        class TaggedItem(models.Model):
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            # missing object_id field
            content_object = GenericForeignKey()

        field = TaggedItem._meta.get_field("content_object")

        self.assertEqual(
            field.check(),
            [
                checks.Error(
                    "The GenericForeignKey object ID references the nonexistent "
                    "field 'object_id'.",
                    obj=field,
                    id="contenttypes.E001",
                )
            ],
        )