def test_from_response_post_nonascii_unicode(self):
        response = _buildresponse(
            """<form action="post.php" method="POST">
            <input type="hidden" name="test £" value="val1">
            <input type="hidden" name="test £" value="val2">
            <input type="hidden" name="test2" value="xxx µ">
            </form>""",
            url="http://www.example.com/this/list.html",
        )
        req = self.request_class.from_response(
            response, formdata={"one": ["two", "three"], "six": "seven"}
        )

        assert req.method == "POST"
        assert req.headers[b"Content-type"] == b"application/x-www-form-urlencoded"
        assert req.url == "http://www.example.com/this/post.php"
        fs = _qs(req, to_unicode=True)
        assert set(fs["test £"]) == {"val1", "val2"}
        assert set(fs["one"]) == {"two", "three"}
        assert fs["test2"] == ["xxx µ"]
        assert fs["six"] == ["seven"]