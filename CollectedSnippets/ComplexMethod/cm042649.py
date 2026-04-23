def test_from_response_get(self):
        response = _buildresponse(
            """<form action="get.php" method="GET">
            <input type="hidden" name="test" value="val1">
            <input type="hidden" name="test" value="val2">
            <input type="hidden" name="test2" value="xxx">
            </form>""",
            url="http://www.example.com/this/list.html",
        )
        r1 = self.request_class.from_response(
            response, formdata={"one": ["two", "three"], "six": "seven"}
        )
        assert r1.method == "GET"
        assert urlparse_cached(r1).hostname == "www.example.com"
        assert urlparse_cached(r1).path == "/this/get.php"
        fs = _qs(r1)
        assert set(fs[b"test"]) == {b"val1", b"val2"}
        assert set(fs[b"one"]) == {b"two", b"three"}
        assert fs[b"test2"] == [b"xxx"]
        assert fs[b"six"] == [b"seven"]