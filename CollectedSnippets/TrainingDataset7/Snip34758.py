def test_single_context(self):
        "Template assertions work when there is a single context"
        response = self.client.get("/post_view/", {})
        msg = (
            ": Template 'Empty GET Template' was used unexpectedly in "
            "rendering the response"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateNotUsed(response, "Empty GET Template")
        with self.assertRaisesMessage(AssertionError, "abc" + msg):
            self.assertTemplateNotUsed(response, "Empty GET Template", msg_prefix="abc")
        msg = (
            ": Template 'Empty POST Template' was not a template used to "
            "render the response. Actual template(s) used: Empty GET Template"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "Empty POST Template")
        with self.assertRaisesMessage(AssertionError, "abc" + msg):
            self.assertTemplateUsed(response, "Empty POST Template", msg_prefix="abc")
        msg = (
            ": Template 'Empty GET Template' was expected to be rendered 2 "
            "time(s) but was actually rendered 1 time(s)."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertTemplateUsed(response, "Empty GET Template", count=2)
        with self.assertRaisesMessage(AssertionError, "abc" + msg):
            self.assertTemplateUsed(
                response, "Empty GET Template", msg_prefix="abc", count=2
            )