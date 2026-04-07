def test_response(self):
        filename = os.path.join(os.path.dirname(__file__), "abc.txt")

        # file isn't closed until we close the response.
        file1 = open(filename)
        r = HttpResponse(file1)
        self.assertTrue(file1.closed)
        r.close()

        # when multiple file are assigned as content, make sure they are all
        # closed with the response.
        file1 = open(filename)
        file2 = open(filename)
        r = HttpResponse(file1)
        r.content = file2
        self.assertTrue(file1.closed)
        self.assertTrue(file2.closed)