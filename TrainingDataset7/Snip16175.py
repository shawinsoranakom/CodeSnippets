def test_success(self):
        q = Question.objects.create(question="Is this a question?")
        request = self.factory.get(self.url, {"term": "is", **self.opts})
        request.user = self.superuser
        response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(
            data,
            {
                "results": [{"id": str(q.pk), "text": q.question}],
                "pagination": {"more": False},
            },
        )