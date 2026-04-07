def test_reverse_by_related_name(self):
        p1 = Poll.objects.get(poll_choice__name__exact="This is the answer.")
        self.assertEqual(p1.question, "What's the first question?")

        p2 = Poll.objects.get(related_choice__name__exact="This is the answer.")
        self.assertEqual(p2.question, "What's the second question?")