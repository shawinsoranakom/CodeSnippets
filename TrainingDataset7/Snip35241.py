def test_assert_used_on_http_response(self):
        response = HttpResponse()
        msg = "%s() is only usable on responses fetched using the Django test Client."
        with self.assertRaisesMessage(ValueError, msg % "assertTemplateUsed"):
            self.assertTemplateUsed(response, "template.html")
        with self.assertRaisesMessage(ValueError, msg % "assertTemplateNotUsed"):
            self.assertTemplateNotUsed(response, "template.html")