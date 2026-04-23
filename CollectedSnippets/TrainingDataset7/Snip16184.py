def test_limit_choices_to(self):
        # Answer.question_with_to_field defines limit_choices_to to "those not
        # starting with 'not'".
        q = Question.objects.create(question="Is this a question?")
        Question.objects.create(question="Not a question.")
        request = self.factory.get(
            self.url,
            {"term": "is", **self.opts, "field_name": "question_with_to_field"},
        )
        request.user = self.superuser
        response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(
            data,
            {
                "results": [{"id": str(q.uuid), "text": q.question}],
                "pagination": {"more": False},
            },
        )