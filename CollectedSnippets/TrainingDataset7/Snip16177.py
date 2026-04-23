def test_custom_to_field_permission_denied(self):
        Question.objects.create(question="Is this a question?")
        request = self.factory.get(
            self.url,
            {"term": "is", **self.opts, "field_name": "question_with_to_field"},
        )
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            AutocompleteJsonView.as_view(**self.as_view_args)(request)