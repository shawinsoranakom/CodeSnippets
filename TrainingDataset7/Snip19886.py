def test_valid_generic_relationship_with_explicit_fields(self):
        class TaggedItem(models.Model):
            custom_content_type = models.ForeignKey(ContentType, models.CASCADE)
            custom_object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey(
                "custom_content_type", "custom_object_id"
            )

        class Bookmark(models.Model):
            tags = GenericRelation(
                "TaggedItem",
                content_type_field="custom_content_type",
                object_id_field="custom_object_id",
            )

        self.assertEqual(Bookmark.tags.field.check(), [])