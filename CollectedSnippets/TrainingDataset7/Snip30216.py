def test_charfield_GFK(self):
        b = Bookmark.objects.create(url="http://www.djangoproject.com/")
        TaggedItem.objects.create(content_object=b, tag="django")
        TaggedItem.objects.create(content_object=b, favorite=b, tag="python")

        with self.assertNumQueries(3):
            bookmark = Bookmark.objects.filter(pk=b.pk).prefetch_related(
                "tags", "favorite_tags"
            )[0]
            self.assertEqual(
                sorted(i.tag for i in bookmark.tags.all()), ["django", "python"]
            )
            self.assertEqual([i.tag for i in bookmark.favorite_tags.all()], ["python"])