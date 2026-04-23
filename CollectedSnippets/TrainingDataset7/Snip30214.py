def test_nullable_GFK(self):
        TaggedItem.objects.create(
            tag="awesome", content_object=self.book1, created_by=self.reader1
        )
        TaggedItem.objects.create(tag="great", content_object=self.book2)
        TaggedItem.objects.create(tag="rubbish", content_object=self.book3)

        with self.assertNumQueries(2):
            result = [
                t.created_by for t in TaggedItem.objects.prefetch_related("created_by")
            ]

        self.assertEqual(result, [t.created_by for t in TaggedItem.objects.all()])