def test_streaming_response(self):
        filename = os.path.join(os.path.dirname(__file__), "abc.txt")

        # file isn't closed until we close the response.
        file1 = open(filename)
        r = StreamingHttpResponse(file1)
        self.assertFalse(file1.closed)
        r.close()
        self.assertTrue(file1.closed)

        # when multiple file are assigned as content, make sure they are all
        # closed with the response.
        file1 = open(filename)
        file2 = open(filename)
        r = StreamingHttpResponse(file1)
        r.streaming_content = file2
        self.assertFalse(file1.closed)
        self.assertFalse(file2.closed)
        r.close()
        self.assertTrue(file1.closed)
        self.assertTrue(file2.closed)