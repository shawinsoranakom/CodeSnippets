def test_set_foreign_key(self):
        """
        You can set a generic foreign key in the way you'd expect.
        """
        tag1 = TaggedItem.objects.create(content_object=self.quartz, tag="shiny")
        tag1.content_object = self.platypus
        tag1.save()

        self.assertSequenceEqual(self.platypus.tags.all(), [tag1])