def test_ticket14729(self):
        # Test representation of raw query with one or few parameters passed as
        # list
        query = "SELECT * FROM queries_note WHERE note = %s"
        params = ["n1"]
        qs = Note.objects.raw(query, params=params)
        self.assertEqual(
            repr(qs), "<RawQuerySet: SELECT * FROM queries_note WHERE note = n1>"
        )

        query = "SELECT * FROM queries_note WHERE note = %s and misc = %s"
        params = ["n1", "foo"]
        qs = Note.objects.raw(query, params=params)
        self.assertEqual(
            repr(qs),
            "<RawQuerySet: SELECT * FROM queries_note WHERE note = n1 and misc = foo>",
        )