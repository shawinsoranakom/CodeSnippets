def test_bulk_create_with_existing_children(self):
        """
        bulk_create() should continue _order sequence from existing children.
        """
        question = self.Question.objects.create(text="Test Question")
        self.Answer.objects.create(question=question, text="Existing 0")
        self.Answer.objects.create(question=question, text="Existing 1")

        new_answers = [
            self.Answer(question=question, text=f"New Answer {i}") for i in range(2)
        ]
        answer2, answer3 = self.Answer.objects.bulk_create(new_answers)

        self.assertEqual(answer2._order, 2)
        self.assertEqual(answer3._order, 3)