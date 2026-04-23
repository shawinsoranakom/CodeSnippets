def test_httprequest_full_path(self):
        request = HttpRequest()
        request.path_info = "/;some/?awful/=path/foo:bar/"
        request.path = "/prefix" + request.path_info
        request.META["QUERY_STRING"] = ";some=query&+query=string"
        expected = "/%3Bsome/%3Fawful/%3Dpath/foo:bar/?;some=query&+query=string"
        self.assertEqual(request.get_full_path_info(), expected)
        self.assertEqual(request.get_full_path(), "/prefix" + expected)