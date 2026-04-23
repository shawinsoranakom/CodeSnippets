def test_body(self):
        r1 = self.request_class(url="http://www.example.com/")
        assert r1.body == b""

        r2 = self.request_class(url="http://www.example.com/", body=b"")
        assert isinstance(r2.body, bytes)
        assert r2.encoding == "utf-8"  # default encoding

        r3 = self.request_class(
            url="http://www.example.com/", body="Price: \xa3100", encoding="utf-8"
        )
        assert isinstance(r3.body, bytes)
        assert r3.body == b"Price: \xc2\xa3100"

        r4 = self.request_class(
            url="http://www.example.com/", body="Price: \xa3100", encoding="latin1"
        )
        assert isinstance(r4.body, bytes)
        assert r4.body == b"Price: \xa3100"