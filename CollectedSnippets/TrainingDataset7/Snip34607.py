def test_notfound_response(self):
        "GET a URL that responds as '404:Not Found'"
        response = self.client.get("/bad_view/")
        self.assertContains(response, "MAGIC", status_code=404)