def test_exclude_generic_relations(self):
        """
        Test lookups over an object without GenericRelations.
        """
        # Recall that the Mineral class doesn't have an explicit
        # GenericRelation defined. That's OK, because you can create
        # TaggedItems explicitly. However, excluding GenericRelations means
        # your lookups have to be a bit more explicit.
        shiny = TaggedItem.objects.create(content_object=self.quartz, tag="shiny")
        clearish = TaggedItem.objects.create(content_object=self.quartz, tag="clearish")

        ctype = ContentType.objects.get_for_model(self.quartz)
        q = TaggedItem.objects.filter(
            content_type__pk=ctype.id, object_id=self.quartz.id
        )
        self.assertSequenceEqual(q, [clearish, shiny])