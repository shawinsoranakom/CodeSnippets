def setUp(self):
        self.req = self.request_factory.get("/")
        self.req.META["HTTP_ACCEPT_ENCODING"] = "gzip, deflate"
        self.req.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (Windows NT 5.1; rv:9.0.1) Gecko/20100101 Firefox/9.0.1"
        )
        self.resp = HttpResponse()
        self.resp.status_code = 200
        self.resp.content = self.compressible_string
        self.resp["Content-Type"] = "text/html; charset=UTF-8"