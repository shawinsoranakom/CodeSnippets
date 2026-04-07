def _create_object(self, model):
        """
        Create a model with an attached Media object via GFK. We can't
        load content via a fixture (since the GenericForeignKey relies on
        content type IDs, which will vary depending on what other tests
        have been run), thus we do it here.
        """
        e = model.objects.create(name="This Week in Django")
        Media.objects.create(content_object=e, url="http://example.com/podcast.mp3")
        return e