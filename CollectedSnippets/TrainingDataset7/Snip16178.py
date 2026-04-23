def test_custom_to_field_custom_pk(self):
        q = Question.objects.create(question="Is this a question?")
        opts = {
            "app_label": Question._meta.app_label,
            "model_name": Question._meta.model_name,
            "field_name": "related_questions",
        }
        request = self.factory.get(self.url, {"term": "is", **opts})
        request.user = self.superuser
        response = AutocompleteJsonView.as_view(**self.as_view_args)(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(
            data,
            {
                "results": [{"id": str(q.big_id), "text": q.question}],
                "pagination": {"more": False},
            },
        )