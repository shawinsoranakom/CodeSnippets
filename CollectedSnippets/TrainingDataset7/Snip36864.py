def test_doc_links(self, mocked_get_complete_version):
        response = self.client.post("/")
        self.assertContains(response, "Forbidden", status_code=403)
        self.assertNotContains(
            response, "https://docs.djangoproject.com/en/dev/", status_code=403
        )
        self.assertContains(
            response, "https://docs.djangoproject.com/en/4.2/", status_code=403
        )