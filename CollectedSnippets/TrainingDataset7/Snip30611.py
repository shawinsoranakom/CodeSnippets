def test_ticket7791(self):
        # There were "issues" when ordering and distinct-ing on fields related
        # via ForeignKeys.
        self.assertEqual(len(Note.objects.order_by("extrainfo__info").distinct()), 3)

        # Pickling of QuerySets using datetimes() should work.
        qs = Item.objects.datetimes("created", "month")
        pickle.loads(pickle.dumps(qs))