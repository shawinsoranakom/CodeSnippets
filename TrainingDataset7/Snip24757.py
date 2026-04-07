def test_handler_renders_template_response(self):
        """
        BaseHandler should render TemplateResponse if necessary.
        """
        response = self.client.get("/")
        self.assertContains(response, "Error handler content", status_code=403)