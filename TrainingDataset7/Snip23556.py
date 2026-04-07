def test_generic_prefetch(self):
        tagged_vegetable = TaggedItem.objects.create(
            tag="great", content_object=self.bacon
        )
        tagged_animal = TaggedItem.objects.create(
            tag="awesome", content_object=self.platypus
        )
        # Getting the instances again so that content object is deferred.
        tagged_vegetable = TaggedItem.objects.get(pk=tagged_vegetable.pk)
        tagged_animal = TaggedItem.objects.get(pk=tagged_animal.pk)

        with self.assertNumQueries(2):
            prefetch_related_objects(
                [tagged_vegetable, tagged_animal],
                GenericPrefetch(
                    "content_object",
                    [Vegetable.objects.all(), Animal.objects.only("common_name")],
                ),
            )
        with self.assertNumQueries(0):
            self.assertEqual(tagged_vegetable.content_object.name, self.bacon.name)
        with self.assertNumQueries(0):
            self.assertEqual(
                tagged_animal.content_object.common_name,
                self.platypus.common_name,
            )
        with self.assertNumQueries(1):
            self.assertEqual(
                tagged_animal.content_object.latin_name,
                self.platypus.latin_name,
            )