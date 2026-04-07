def test_closed(self):
        r = HttpResponseBase()
        self.assertIs(r.closed, False)

        r.close()
        self.assertIs(r.closed, True)