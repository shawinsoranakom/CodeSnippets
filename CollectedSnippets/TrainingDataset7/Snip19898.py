def test_clear_cached_generic_relation_explicit_fields(self):
        question = Question.objects.create(text="question")
        answer = Answer.objects.create(text="answer", question=question)
        old_question_obj = answer.question
        # The reverse relation is not refreshed if not passed explicitly in
        # `fields`.
        answer.refresh_from_db(fields=["text"])
        self.assertIs(answer.question, old_question_obj)
        answer.refresh_from_db(fields=["question"])
        self.assertIsNot(answer.question, old_question_obj)
        self.assertEqual(answer.question, old_question_obj)