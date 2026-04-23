def test_not_modified_repr(self):
        response = HttpResponseNotModified()
        self.assertEqual(repr(response), "<HttpResponseNotModified status_code=304>")