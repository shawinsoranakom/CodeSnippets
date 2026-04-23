def test_item_ordering(self):
        # We can retrieve the ordering of the queryset from a particular item.
        a1 = self.q1.answer_set.all()[1]
        id_list = [o.pk for o in self.q1.answer_set.all()]
        self.assertSequenceEqual(a1.question.get_answer_order(), id_list)

        # It doesn't matter which answer we use to check the order, it will
        # always be the same.
        a2 = self.Answer.objects.create(text="Number five", question=self.q1)
        self.assertEqual(
            list(a1.question.get_answer_order()), list(a2.question.get_answer_order())
        )