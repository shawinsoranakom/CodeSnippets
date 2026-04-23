def test_modify_context_and_render(self):
        template = Template("{{ foo }}")
        request = self.request_factory.get("/")
        context = RequestContext(request, {})
        context["foo"] = "foo"
        self.assertEqual(template.render(context), "foo")