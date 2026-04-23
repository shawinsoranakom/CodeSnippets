def test_ticket_21150(self):
        b = Bravo.objects.create()
        c = Charlie.objects.create(bravo=b)
        qs = Charlie.objects.select_related("alfa").annotate(Count("bravo__charlie"))
        self.assertSequenceEqual(qs, [c])
        self.assertIs(qs[0].alfa, None)
        a = Alfa.objects.create()
        c.alfa = a
        c.save()
        # Force re-evaluation
        qs = qs.all()
        self.assertSequenceEqual(qs, [c])
        self.assertEqual(qs[0].alfa, a)