def test_empty_content_length(self):
        self.request.environ["CONTENT_LENGTH"] = ""
        self.request.body