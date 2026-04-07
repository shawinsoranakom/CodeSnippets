def test_field_name_ending_with_underscore(self):
        class TaggedItem(models.Model):
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey()

        class InvalidBookmark(models.Model):
            tags_ = GenericRelation("TaggedItem")

        self.assertEqual(
            InvalidBookmark.tags_.field.check(),
            [
                checks.Error(
                    "Field names must not end with an underscore.",
                    obj=InvalidBookmark.tags_.field,
                    id="fields.E001",
                )
            ],
        )