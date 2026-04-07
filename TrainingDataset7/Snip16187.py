def test_search_use_distinct(self):
        """
        Searching across model relations use QuerySet.distinct() to avoid
        duplicates.
        """
        q1 = Question.objects.create(question="question 1")
        q2 = Question.objects.create(question="question 2")
        q2.related_questions.add(q1)
        q3 = Question.objects.create(question="question 3")
        q3.related_questions.add(q1)
        request = self.factory.get(self.url, {"term": "question", **self.opts})
        request.user = self.superuser

        class DistinctQuestionAdmin(QuestionAdmin):
            search_fields = ["related_questions__question", "question"]

        with model_admin(Question, DistinctQuestionAdmin):
            response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(len(data["results"]), 3)