def test_url_namespace02(self):
        request = self.request_factory.get("/")
        request.resolver_match = resolve("/ns2/")
        template = self.engine.get_template("url-namespace02")
        context = RequestContext(request)
        output = template.render(context)
        self.assertEqual(output, "/ns2/named-client/42/")