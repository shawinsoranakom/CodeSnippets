def test_field_does_not_allowed(self):
        request = self.factory.get(
            self.url, {"term": "is", **self.opts, "field_name": "related_questions"}
        )
        request.user = self.superuser
        with self.assertRaises(PermissionDenied):
            AutocompleteJsonView.as_view(**self.as_view_args)(request)