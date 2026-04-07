def test_generic_relations(self):
        with self.assertRaisesMessage(FieldError, self.invalid_error % ("tags", "")):
            list(Bookmark.objects.select_related("tags"))

        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("content_object", "content_type")
        ):
            list(TaggedItem.objects.select_related("content_object"))