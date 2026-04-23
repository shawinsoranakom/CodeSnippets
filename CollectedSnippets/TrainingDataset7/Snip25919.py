def test_multiple_m2m(self):
        # Multiple m2m references to model must be distinguished when
        # accessing the relations through an instance attribute.

        s1 = SelfRefer.objects.create(name="s1")
        s2 = SelfRefer.objects.create(name="s2")
        s3 = SelfRefer.objects.create(name="s3")
        s1.references.add(s2)
        s1.related.add(s3)

        e1 = Entry.objects.create(name="e1")
        t1 = Tag.objects.create(name="t1")
        t2 = Tag.objects.create(name="t2")

        e1.topics.add(t1)
        e1.related.add(t2)

        self.assertSequenceEqual(s1.references.all(), [s2])
        self.assertSequenceEqual(s1.related.all(), [s3])

        self.assertSequenceEqual(e1.topics.all(), [t1])
        self.assertSequenceEqual(e1.related.all(), [t2])