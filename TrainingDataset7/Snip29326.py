def test_bulk_create_mixed_scenario(self):
        """
        The _order field should be correctly set for new Answer objects based
        on the count of existing Answers for each related Question.
        """
        question0 = self.Question.objects.create(text="Question 0")
        question1 = self.Question.objects.create(text="Question 1")

        self.Answer.objects.create(question=question1, text="Q1 Existing 0")
        self.Answer.objects.create(question=question1, text="Q1 Existing 1")

        new_answers = [
            self.Answer(question=question0, text="Q0 New 0"),
            self.Answer(question=question1, text="Q1 New 0"),
            self.Answer(question=question0, text="Q0 New 1"),
        ]
        created_answers = self.Answer.objects.bulk_create(new_answers)
        answer_q0_0, answer_q1_2, answer_q0_1 = created_answers

        self.assertEqual(answer_q0_0._order, 0)
        self.assertEqual(answer_q0_1._order, 1)
        self.assertEqual(answer_q1_2._order, 2)