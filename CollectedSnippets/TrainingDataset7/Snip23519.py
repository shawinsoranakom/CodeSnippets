def test_add_bulk(self):
        bacon = Vegetable.objects.create(name="Bacon", is_yucky=False)
        t1 = TaggedItem.objects.create(content_object=self.quartz, tag="shiny")
        t2 = TaggedItem.objects.create(content_object=self.quartz, tag="clearish")
        # One update() query.
        with self.assertNumQueries(1):
            bacon.tags.add(t1, t2)
        self.assertEqual(t1.content_object, bacon)
        self.assertEqual(t2.content_object, bacon)