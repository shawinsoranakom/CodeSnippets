def test_set_order_unrelated_object(self):
        """An answer that's not related isn't updated."""
        q = self.Question.objects.create(text="other")
        a = self.Answer.objects.create(text="Number five", question=q)
        self.q1.set_answer_order([o.pk for o in self.q1.answer_set.all()] + [a.pk])
        self.assertEqual(self.Answer.objects.get(pk=a.pk)._order, 0)