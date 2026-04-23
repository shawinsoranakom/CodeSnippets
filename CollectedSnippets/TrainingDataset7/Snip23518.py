def test_tag_deletion_related_objects_unaffected(self):
        """
        If you delete a tag, the objects using the tag are unaffected (other
        than losing a tag).
        """
        ctype = ContentType.objects.get_for_model(self.lion)
        tag = TaggedItem.objects.get(
            content_type__pk=ctype.id, object_id=self.lion.id, tag="hairy"
        )
        tag.delete()

        self.assertSequenceEqual(self.lion.tags.all(), [self.yellow])
        self.assertQuerySetEqual(
            TaggedItem.objects.all(),
            [
                ("fatty", Vegetable, self.bacon.pk),
                ("salty", Vegetable, self.bacon.pk),
                ("yellow", Animal, self.lion.pk),
            ],
            self.comp_func,
        )