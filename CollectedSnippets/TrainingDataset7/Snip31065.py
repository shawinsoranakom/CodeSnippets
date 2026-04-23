def test_httprequest_full_path_with_query_string_and_fragment(self):
        request = HttpRequest()
        request.path_info = "/foo#bar"
        request.path = "/prefix" + request.path_info
        request.META["QUERY_STRING"] = "baz#quux"
        self.assertEqual(request.get_full_path_info(), "/foo%23bar?baz#quux")
        self.assertEqual(request.get_full_path(), "/prefix/foo%23bar?baz#quux")