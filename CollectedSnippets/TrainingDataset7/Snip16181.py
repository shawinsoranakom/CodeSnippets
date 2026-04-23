def test_field_does_not_exist(self):
        request = self.factory.get(
            self.url, {"term": "is", **self.opts, "field_name": "does_not_exist"}
        )
        request.user = self.superuser
        with self.assertRaises(PermissionDenied):
            AutocompleteJsonView.as_view(**self.as_view_args)(request)