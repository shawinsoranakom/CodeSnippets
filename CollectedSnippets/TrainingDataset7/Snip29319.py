def test_change_ordering(self):
        # The ordering can be altered
        a = self.Answer.objects.create(text="Number five", question=self.q1)

        # Swap the last two items in the order list
        id_list = [o.pk for o in self.q1.answer_set.all()]
        x = id_list.pop()
        id_list.insert(-1, x)

        # By default, the ordering is different from the swapped version
        self.assertNotEqual(list(a.question.get_answer_order()), id_list)

        # Change the ordering to the swapped version -
        # this changes the ordering of the queryset.
        a.question.set_answer_order(id_list)
        self.assertQuerySetEqual(
            self.q1.answer_set.all(),
            ["John", "Paul", "George", "Number five", "Ringo"],
            attrgetter("text"),
        )