def test_url_namespace03(self):
        request = self.request_factory.get("/")
        template = self.engine.get_template("url-namespace03")
        context = RequestContext(request)
        output = template.render(context)
        self.assertEqual(output, "/ns2/named-client/42/")