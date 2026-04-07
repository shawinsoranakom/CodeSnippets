def test_missing_content_type_field(self):
        class TaggedItem(models.Model):
            # no content_type field
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey()

        field = TaggedItem._meta.get_field("content_object")

        expected = [
            checks.Error(
                "The GenericForeignKey content type references the nonexistent "
                "field 'TaggedItem.content_type'.",
                obj=field,
                id="contenttypes.E002",
            )
        ]
        self.assertEqual(field.check(), expected)