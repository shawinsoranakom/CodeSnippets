def test_ticket10432(self):
        # Using an empty iterator as the rvalue for an "__in"
        # lookup is legal.
        self.assertCountEqual(Note.objects.filter(pk__in=iter(())), [])