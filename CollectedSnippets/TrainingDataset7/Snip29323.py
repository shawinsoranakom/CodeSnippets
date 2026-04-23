def test_bulk_create_with_empty_parent(self):
        """
        bulk_create() should properly set _order when parent has no existing
        children.
        """
        question = self.Question.objects.create(text="Test Question")
        answers = [self.Answer(question=question, text=f"Answer {i}") for i in range(3)]
        answer0, answer1, answer2 = self.Answer.objects.bulk_create(answers)

        self.assertEqual(answer0._order, 0)
        self.assertEqual(answer1._order, 1)
        self.assertEqual(answer2._order, 2)