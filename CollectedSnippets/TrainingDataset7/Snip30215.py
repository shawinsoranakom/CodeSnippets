def test_generic_relation(self):
        bookmark = Bookmark.objects.create(url="http://www.djangoproject.com/")
        TaggedItem.objects.create(content_object=bookmark, tag="django")
        TaggedItem.objects.create(content_object=bookmark, tag="python")

        with self.assertNumQueries(2):
            tags = [
                t.tag
                for b in Bookmark.objects.prefetch_related("tags")
                for t in b.tags.all()
            ]
            self.assertEqual(sorted(tags), ["django", "python"])