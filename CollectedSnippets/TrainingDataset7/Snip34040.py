def test_url_namespace01(self):
        request = self.request_factory.get("/")
        request.resolver_match = resolve("/ns1/")
        template = self.engine.get_template("url-namespace01")
        context = RequestContext(request)
        output = template.render(context)
        self.assertEqual(output, "/ns1/named-client/42/")