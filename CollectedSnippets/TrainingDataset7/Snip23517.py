def test_object_deletion_without_generic_relation(self):
        """
        If Generic Relation is not explicitly defined, any related objects
        remain after deletion of the source object.
        """
        TaggedItem.objects.create(content_object=self.quartz, tag="clearish")
        quartz_pk = self.quartz.pk
        self.quartz.delete()
        self.assertQuerySetEqual(
            TaggedItem.objects.all(),
            [
                ("clearish", Mineral, quartz_pk),
                ("fatty", Vegetable, self.bacon.pk),
                ("hairy", Animal, self.lion.pk),
                ("salty", Vegetable, self.bacon.pk),
                ("yellow", Animal, self.lion.pk),
            ],
            self.comp_func,
        )