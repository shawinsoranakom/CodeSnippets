def test_ticket_11293_q_immutable(self):
        """
        Splitting a q object to parts for where/having doesn't alter
        the original q-object.
        """
        q1 = Q(isbn="")
        q2 = Q(authors__count__gt=1)
        query = Book.objects.annotate(Count("authors"))
        query.filter(q1 | q2)
        self.assertEqual(len(q2.children), 1)