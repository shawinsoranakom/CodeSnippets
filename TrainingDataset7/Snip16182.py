def test_field_no_related_field(self):
        request = self.factory.get(
            self.url, {"term": "is", **self.opts, "field_name": "answer"}
        )
        request.user = self.superuser
        with self.assertRaises(PermissionDenied):
            AutocompleteJsonView.as_view(**self.as_view_args)(request)