def test_tickets_8921_9188(self):
        # Incorrect SQL was being generated for certain types of exclude()
        # queries that crossed multi-valued relations (#8921, #9188 and some
        # preemptively discovered cases).

        self.assertSequenceEqual(
            PointerA.objects.filter(connection__pointerb__id=1), []
        )
        self.assertSequenceEqual(
            PointerA.objects.exclude(connection__pointerb__id=1), []
        )

        self.assertSequenceEqual(
            Tag.objects.exclude(children=None),
            [self.t1, self.t3],
        )

        # This example is tricky because the parent could be NULL, so only
        # checking parents with annotations omits some results (tag t1, in this
        # case).
        self.assertSequenceEqual(
            Tag.objects.exclude(parent__annotation__name="a1"),
            [self.t1, self.t4, self.t5],
        )

        # The annotation->tag link is single values and tag->children links is
        # multi-valued. So we have to split the exclude filter in the middle
        # and then optimize the inner query without losing results.
        self.assertSequenceEqual(
            Annotation.objects.exclude(tag__children__name="t2"),
            [self.ann2],
        )

        # Nested queries are possible (although should be used with care, since
        # they have performance problems on backends like MySQL.
        self.assertSequenceEqual(
            Annotation.objects.filter(notes__in=Note.objects.filter(note="n1")),
            [self.ann1],
        )