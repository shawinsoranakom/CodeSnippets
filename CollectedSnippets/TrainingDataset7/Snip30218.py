def test_deleted_GFK(self):
        TaggedItem.objects.create(tag="awesome", content_object=self.book1)
        TaggedItem.objects.create(tag="awesome", content_object=self.book2)
        ct = ContentType.objects.get_for_model(Book)

        book1_pk = self.book1.pk
        self.book1.delete()

        with self.assertNumQueries(2):
            qs = TaggedItem.objects.filter(tag="awesome").prefetch_related(
                "content_object"
            )
            result = [
                (tag.object_id, tag.content_type_id, tag.content_object) for tag in qs
            ]
            self.assertEqual(
                result,
                [
                    (book1_pk, ct.pk, None),
                    (self.book2.pk, ct.pk, self.book2),
                ],
            )