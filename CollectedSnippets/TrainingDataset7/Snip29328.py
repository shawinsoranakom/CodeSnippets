def test_bulk_create_allows_duplicate_order_values(self):
        """
        bulk_create() should allow duplicate _order values if the model
        does not enforce uniqueness on the _order field.
        """
        question = self.Question.objects.create(text="Duplicated Test")

        # Existing answer to set initial _order=0.
        self.Answer.objects.create(question=question, text="Existing Answer")
        # Two manually set _order=1 and one auto (which may also be assigned
        # 1).
        answers = [
            self.Answer(question=question, text="Manual Order 1", _order=1),
            self.Answer(question=question, text="Auto Order 1"),
            self.Answer(question=question, text="Auto Order 2"),
            self.Answer(question=question, text="Manual Order 1 Duplicate", _order=1),
        ]

        created_answers = self.Answer.objects.bulk_create(answers)
        manual_1, auto_1, auto_2, manual_2 = created_answers

        # Manual values are as assigned, even if duplicated.
        self.assertEqual(manual_1._order, 1)
        self.assertEqual(manual_2._order, 1)
        # Auto-assigned orders may also use 1 or any value, depending on
        # implementation. If no collision logic, they may overlap with manual
        # values.
        self.assertEqual(auto_1._order, 1)
        self.assertEqual(auto_2._order, 2)