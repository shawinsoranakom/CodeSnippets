def test_technical_404_converter_raise_404(self):
        with mock.patch.object(IntConverter, "to_python", side_effect=Http404):
            response = self.client.get("/path-post/1/")
            self.assertContains(response, "Page not found", status_code=404)