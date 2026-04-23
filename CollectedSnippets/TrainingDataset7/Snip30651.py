def test_ticket24525(self):
        tag = Tag.objects.create()
        anth100 = tag.note_set.create(note="ANTH", misc="100")
        math101 = tag.note_set.create(note="MATH", misc="101")
        s1 = tag.annotation_set.create(name="1")
        s2 = tag.annotation_set.create(name="2")
        s1.notes.set([math101, anth100])
        s2.notes.set([math101])
        result = math101.annotation_set.all() & tag.annotation_set.exclude(
            notes__in=[anth100]
        )
        self.assertEqual(list(result), [s2])