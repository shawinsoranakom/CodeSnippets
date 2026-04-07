def test_clear_cached_generic_relation_when_deferred(self):
        question = Question.objects.create(text="question")
        Answer.objects.create(text="answer", question=question)
        answer = Answer.objects.defer("text").get()
        old_question_obj = answer.question
        # The reverse relation is refreshed even when the text field is
        # deferred.
        answer.refresh_from_db()
        self.assertIsNot(answer.question, old_question_obj)