def test_ticket_24278(self):
        School.objects.create()
        qs = School.objects.filter(Q(pk__in=()) | Q())
        self.assertSequenceEqual(qs, [])