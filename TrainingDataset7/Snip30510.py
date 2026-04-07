def test_intersection_in_nested_subquery(self):
        tag = Tag.objects.create(name="tag")
        note = Note.objects.create(tag=tag)
        annotation = Annotation.objects.create(tag=tag)
        tags = Tag.objects.order_by()
        tags = tags.filter(id=OuterRef("tag_id")).intersection(
            tags.filter(id=OuterRef(OuterRef("tag_id")))
        )
        qs = Note.objects.filter(
            Exists(Annotation.objects.filter(Exists(tags), notes=OuterRef("pk")))
        )
        self.assertIsNone(qs.first())
        annotation.notes.add(note)
        self.assertEqual(qs.first(), note)