def test_redirect(self):
        response = HttpResponseRedirect("/redirected/")
        self.assertEqual(response.status_code, 302)
        # Standard HttpResponse init args can be used
        response = HttpResponseRedirect(
            "/redirected/",
            content="The resource has temporarily moved",
        )
        self.assertContains(
            response, "The resource has temporarily moved", status_code=302
        )
        self.assertEqual(response.url, response.headers["Location"])