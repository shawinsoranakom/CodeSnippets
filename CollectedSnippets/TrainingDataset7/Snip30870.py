def test_ticket_20101(self):
        """
        Tests QuerySet ORed combining in exclude subquery case.
        """
        t = Tag.objects.create(name="foo")
        a1 = Annotation.objects.create(tag=t, name="a1")
        a2 = Annotation.objects.create(tag=t, name="a2")
        a3 = Annotation.objects.create(tag=t, name="a3")
        n = Note.objects.create(note="foo", misc="bar")
        qs1 = Note.objects.exclude(annotation__in=[a1, a2])
        qs2 = Note.objects.filter(annotation__in=[a3])
        self.assertIn(n, qs1)
        self.assertNotIn(n, qs2)
        self.assertIn(n, (qs1 | qs2))