def test_bulk_create_multiple_parents(self):
        """
        bulk_create() should maintain separate _order sequences for different
        parents.
        """
        question0 = self.Question.objects.create(text="Question 0")
        question1 = self.Question.objects.create(text="Question 1")

        answers = [
            self.Answer(question=question0, text="Q0 Answer 0"),
            self.Answer(question=question1, text="Q1 Answer 0"),
            self.Answer(question=question0, text="Q0 Answer 1"),
            self.Answer(question=question1, text="Q1 Answer 1"),
        ]
        created_answers = self.Answer.objects.bulk_create(answers)
        answer_q0_0, answer_q1_0, answer_q0_1, answer_q1_1 = created_answers

        self.assertEqual(answer_q0_0._order, 0)
        self.assertEqual(answer_q0_1._order, 1)
        self.assertEqual(answer_q1_0._order, 0)
        self.assertEqual(answer_q1_1._order, 1)