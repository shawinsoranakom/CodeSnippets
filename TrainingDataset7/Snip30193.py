def test_generic_rel(self):
        bookmark = Bookmark.objects.create(url="http://www.djangoproject.com/")
        TaggedItem.objects.create(content_object=bookmark, tag="django")
        TaggedItem.objects.create(
            content_object=bookmark, favorite=bookmark, tag="python"
        )

        # Control lookups.
        with self.assertNumQueries(4):
            lst1 = self.traverse_qs(
                Bookmark.objects.prefetch_related(
                    "tags", "tags__content_object", "favorite_tags"
                ),
                [["tags", "content_object"], ["favorite_tags"]],
            )

        # Test lookups.
        with self.assertNumQueries(4):
            lst2 = self.traverse_qs(
                Bookmark.objects.prefetch_related(
                    Prefetch("tags", to_attr="tags_lst"),
                    Prefetch("tags_lst__content_object"),
                    Prefetch("favorite_tags"),
                ),
                [["tags_lst", "content_object"], ["favorite_tags"]],
            )
        self.assertEqual(lst1, lst2)