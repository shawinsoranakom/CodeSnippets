def test_bulk_create_respects_mixed_manual_order(self):
        """
        bulk_create() should assign _order automatically only for instances
        where it is not manually set. Mixed objects with and without _order
        should result in expected final order values.
        """
        question_a = self.Question.objects.create(text="Question A")
        question_b = self.Question.objects.create(text="Question B")

        # Existing answers to push initial _order forward.
        self.Answer.objects.create(question=question_a, text="Q-A Existing 0")
        self.Answer.objects.create(question=question_b, text="Q-B Existing 0")
        self.Answer.objects.create(question=question_b, text="Q-B Existing 1")

        answers = [
            self.Answer(question=question_a, text="Q-A Manual 4", _order=4),
            self.Answer(question=question_b, text="Q-B Auto 2"),
            self.Answer(question=question_a, text="Q-A Auto"),
            self.Answer(question=question_b, text="Q-B Manual 10", _order=10),
            self.Answer(question=question_a, text="Q-A Manual 7", _order=7),
            self.Answer(question=question_b, text="Q-B Auto 3"),
        ]

        created_answers = self.Answer.objects.bulk_create(answers)
        (
            qa_manual_4,
            qb_auto_2,
            qa_auto,
            qb_manual_10,
            qa_manual_7,
            qb_auto_3,
        ) = created_answers

        # Manual values should stay untouched.
        self.assertEqual(qa_manual_4._order, 4)
        self.assertEqual(qb_manual_10._order, 10)
        self.assertEqual(qa_manual_7._order, 7)
        # Existing max was 0 → auto should get _order=1.
        self.assertEqual(qa_auto._order, 1)
        # Existing max was 1 → next auto gets 2, then 3 (manual 10 is skipped).
        self.assertEqual(qb_auto_2._order, 2)
        self.assertEqual(qb_auto_3._order, 3)