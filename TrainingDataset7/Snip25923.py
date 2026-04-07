def test_create_copy_with_m2m(self):
        t1 = Tag.objects.create(name="t1")
        Entry.objects.create(name="e1")
        entry = Entry.objects.first()
        entry.topics.set([t1])
        old_topics = entry.topics.all()
        entry.pk = None
        entry._state.adding = True
        entry.save()
        entry.topics.set(old_topics)
        entry = Entry.objects.get(pk=entry.pk)
        self.assertCountEqual(entry.topics.all(), old_topics)
        self.assertSequenceEqual(entry.topics.all(), [t1])