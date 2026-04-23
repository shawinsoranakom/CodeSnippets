def test_request_with_items_key(self):
        """
        An exception report can be generated for requests with 'items' in
        request GET, POST, FILES, or COOKIES QueryDicts.
        """
        # GET
        request = self.rf.get("/test_view/?items=Oops")
        reporter = ExceptionReporter(request, None, None, None)
        text = reporter.get_traceback_text()
        self.assertIn("items = 'Oops'", text)
        # POST
        request = self.rf.post("/test_view/", data={"items": "Oops"})
        reporter = ExceptionReporter(request, None, None, None)
        text = reporter.get_traceback_text()
        self.assertIn("items = 'Oops'", text)
        # FILES
        fp = StringIO("filecontent")
        request = self.rf.post("/test_view/", data={"name": "filename", "items": fp})
        reporter = ExceptionReporter(request, None, None, None)
        text = reporter.get_traceback_text()
        self.assertIn("items = <InMemoryUploadedFile:", text)
        # COOKIES
        rf = RequestFactory()
        rf.cookies["items"] = "Oops"
        request = rf.get("/test_view/")
        reporter = ExceptionReporter(request, None, None, None)
        text = reporter.get_traceback_text()
        self.assertIn("items = 'Oops'", text)