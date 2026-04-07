def test_get_paginator(self):
        """Search results are paginated."""

        class PKOrderingQuestionAdmin(QuestionAdmin):
            ordering = ["pk"]

        Question.objects.bulk_create(
            Question(question=str(i)) for i in range(PAGINATOR_SIZE + 10)
        )
        # The first page of results.
        request = self.factory.get(self.url, {"term": "", **self.opts})
        request.user = self.superuser
        with model_admin(Question, PKOrderingQuestionAdmin):
            response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(
            data,
            {
                "results": [
                    {"id": str(q.pk), "text": q.question}
                    for q in Question.objects.all()[:PAGINATOR_SIZE]
                ],
                "pagination": {"more": True},
            },
        )
        # The second page of results.
        request = self.factory.get(self.url, {"term": "", "page": "2", **self.opts})
        request.user = self.superuser
        with model_admin(Question, PKOrderingQuestionAdmin):
            response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(
            data,
            {
                "results": [
                    {"id": str(q.pk), "text": q.question}
                    for q in Question.objects.all()[PAGINATOR_SIZE:]
                ],
                "pagination": {"more": False},
            },
        )