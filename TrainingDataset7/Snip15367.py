def test_model_detail_title(self):
        self.assertContains(self.response, "<h1>admin_docs.Person</h1>", html=True)