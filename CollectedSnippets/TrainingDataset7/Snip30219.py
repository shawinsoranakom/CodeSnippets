def test_reverse_generic_relation(self):
        # Create two distinct bookmarks to ensure the bookmark and
        # tagged item models primary are offset.
        first_bookmark = Bookmark.objects.create()
        second_bookmark = Bookmark.objects.create()
        TaggedItem.objects.create(
            content_object=first_bookmark, favorite=second_bookmark
        )
        with self.assertNumQueries(2):
            obj = TaggedItem.objects.prefetch_related("favorite_bookmarks").get()
        with self.assertNumQueries(0):
            prefetched_bookmarks = obj.favorite_bookmarks.all()
            self.assertQuerySetEqual(prefetched_bookmarks, [second_bookmark])