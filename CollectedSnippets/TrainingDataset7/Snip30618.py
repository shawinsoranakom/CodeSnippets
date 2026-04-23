def test_ticket7181(self):
        # Ordering by related tables should accommodate nullable fields (this
        # test is a little tricky, since NULL ordering is database dependent.
        # Instead, we just count the number of results).
        self.assertEqual(len(Tag.objects.order_by("parent__name")), 5)

        # Empty querysets can be merged with others.
        self.assertSequenceEqual(
            Note.objects.none() | Note.objects.all(),
            [self.n1, self.n2, self.n3],
        )
        self.assertSequenceEqual(
            Note.objects.all() | Note.objects.none(),
            [self.n1, self.n2, self.n3],
        )
        self.assertSequenceEqual(Note.objects.none() & Note.objects.all(), [])
        self.assertSequenceEqual(Note.objects.all() & Note.objects.none(), [])