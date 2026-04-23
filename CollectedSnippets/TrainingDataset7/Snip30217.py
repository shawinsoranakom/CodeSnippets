def test_custom_queryset(self):
        bookmark = Bookmark.objects.create(url="http://www.djangoproject.com/")
        django_tag = TaggedItem.objects.create(content_object=bookmark, tag="django")
        TaggedItem.objects.create(content_object=bookmark, tag="python")

        with self.assertNumQueries(2):
            bookmark = Bookmark.objects.prefetch_related(
                Prefetch("tags", TaggedItem.objects.filter(tag="django")),
            ).get()

        with self.assertNumQueries(0):
            self.assertEqual(list(bookmark.tags.all()), [django_tag])

        # The custom queryset filters should be applied to the queryset
        # instance returned by the manager.
        self.assertEqual(list(bookmark.tags.all()), list(bookmark.tags.all().all()))