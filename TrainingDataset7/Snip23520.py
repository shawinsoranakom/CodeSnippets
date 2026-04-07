def test_add_bulk_false(self):
        bacon = Vegetable.objects.create(name="Bacon", is_yucky=False)
        t1 = TaggedItem.objects.create(content_object=self.quartz, tag="shiny")
        t2 = TaggedItem.objects.create(content_object=self.quartz, tag="clearish")
        # One save() for each object.
        with self.assertNumQueries(2):
            bacon.tags.add(t1, t2, bulk=False)
        self.assertEqual(t1.content_object, bacon)
        self.assertEqual(t2.content_object, bacon)