def test_from_response_post_nonascii_bytes_latin1(self):
        response = _buildresponse(
            b"""<form action="post.php" method="POST">
            <input type="hidden" name="test \xa3" value="val1">
            <input type="hidden" name="test \xa3" value="val2">
            <input type="hidden" name="test2" value="xxx \xb5">
            </form>""",
            url="http://www.example.com/this/list.html",
            encoding="latin1",
        )
        req = self.request_class.from_response(
            response, formdata={"one": ["two", "three"], "six": "seven"}
        )

        assert req.method == "POST"
        assert req.headers[b"Content-type"] == b"application/x-www-form-urlencoded"
        assert req.url == "http://www.example.com/this/post.php"
        fs = _qs(req, to_unicode=True, encoding="latin1")
        assert set(fs["test £"]) == {"val1", "val2"}
        assert set(fs["one"]) == {"two", "three"}
        assert fs["test2"] == ["xxx µ"]
        assert fs["six"] == ["seven"]