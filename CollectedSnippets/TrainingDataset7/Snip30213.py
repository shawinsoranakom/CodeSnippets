def test_traverse_GFK(self):
        """
        A 'content_object' can be traversed with prefetch_related() and
        get to related objects on the other side (assuming it is suitably
        filtered)
        """
        TaggedItem.objects.create(tag="awesome", content_object=self.book1)
        TaggedItem.objects.create(tag="awesome", content_object=self.book2)
        TaggedItem.objects.create(tag="awesome", content_object=self.book3)
        TaggedItem.objects.create(tag="awesome", content_object=self.reader1)
        TaggedItem.objects.create(tag="awesome", content_object=self.reader2)

        ct = ContentType.objects.get_for_model(Book)

        # We get 3 queries - 1 for main query, 1 for content_objects since they
        # all use the same table, and 1 for the 'read_by' relation.
        with self.assertNumQueries(3):
            # If we limit to books, we know that they will have 'read_by'
            # attributes, so the following makes sense:
            qs = TaggedItem.objects.filter(
                content_type=ct, tag="awesome"
            ).prefetch_related("content_object__read_by")
            readers_of_awesome_books = {
                r.name for tag in qs for r in tag.content_object.read_by.all()
            }
            self.assertEqual(readers_of_awesome_books, {"me", "you", "someone"})