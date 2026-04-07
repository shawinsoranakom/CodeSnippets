def test_object_deletion_with_generic_relation(self):
        """
        If you delete an object with an explicit Generic relation, the related
        objects are deleted when the source object is deleted.
        """
        self.assertQuerySetEqual(
            TaggedItem.objects.all(),
            [
                ("fatty", Vegetable, self.bacon.pk),
                ("hairy", Animal, self.lion.pk),
                ("salty", Vegetable, self.bacon.pk),
                ("yellow", Animal, self.lion.pk),
            ],
            self.comp_func,
        )
        self.lion.delete()

        self.assertQuerySetEqual(
            TaggedItem.objects.all(),
            [
                ("fatty", Vegetable, self.bacon.pk),
                ("salty", Vegetable, self.bacon.pk),
            ],
            self.comp_func,
        )