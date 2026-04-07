def test_render_to_string_with_request(self):
        request = RequestFactory().get("/foobar/")
        content = render_to_string("template_loader/request.html", request=request)
        self.assertEqual(content, "/foobar/\n")