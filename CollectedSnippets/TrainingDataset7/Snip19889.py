def test_missing_generic_foreign_key(self):
        class TaggedItem(models.Model):
            content_type = models.ForeignKey(ContentType, models.CASCADE)
            object_id = models.PositiveIntegerField()

        class Bookmark(models.Model):
            tags = GenericRelation("TaggedItem")

        self.assertEqual(
            Bookmark.tags.field.check(),
            [
                checks.Error(
                    "The GenericRelation defines a relation with the model "
                    "'contenttypes_tests.TaggedItem', but that model does not have a "
                    "GenericForeignKey.",
                    obj=Bookmark.tags.field,
                    id="contenttypes.E004",
                )
            ],
        )