def test_multiple_context(self):
        "Template assertions work when there are multiple contexts"
        post_data = {
            "text": "Hello World",
            "email": "foo@example.com",
            "value": 37,
            "single": "b",
            "multi": ("b", "c", "e"),
        }
        response = self.client.post("/form_view_with_template/", post_data)
        self.assertContains(response, "POST data OK")
        msg = "Template '%s' was used unexpectedly in rendering the response"
        with self.assertRaisesMessage(AssertionError, msg % "form_view.html"):
            self.assertTemplateNotUsed(response, "form_view.html")
        with self.assertRaisesMessage(AssertionError, msg % "base.html"):
            self.assertTemplateNotUsed(response, "base.html")
        msg = (
            "Template 'Valid POST Template' was not a template used to render "
            "the response. Actual template(s) used: form_view.html, base.html"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "Valid POST Template")
        msg = (
            "Template 'base.html' was expected to be rendered 2 time(s) but "
            "was actually rendered 1 time(s)."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "base.html", count=2)