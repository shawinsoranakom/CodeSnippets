def test_url_namespace_no_current_app(self):
        request = self.request_factory.get("/")
        request.resolver_match = resolve("/ns1/")
        request.current_app = None
        template = self.engine.get_template("url-namespace-no-current-app")
        context = RequestContext(request)
        output = template.render(context)
        self.assertEqual(output, "/ns2/named-client/42/")