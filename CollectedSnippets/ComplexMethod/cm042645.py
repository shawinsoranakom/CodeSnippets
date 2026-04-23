def test_from_response_post(self):
        response = _buildresponse(
            b"""<form action="post.php" method="POST">
            <input type="hidden" name="test" value="val1">
            <input type="hidden" name="test" value="val2">
            <input type="hidden" name="test2" value="xxx">
            </form>""",
            url="http://www.example.com/this/list.html",
        )
        req = self.request_class.from_response(
            response, formdata={"one": ["two", "three"], "six": "seven"}
        )

        assert req.method == "POST"
        assert req.headers[b"Content-type"] == b"application/x-www-form-urlencoded"
        assert req.url == "http://www.example.com/this/post.php"
        fs = _qs(req)
        assert set(fs[b"test"]) == {b"val1", b"val2"}
        assert set(fs[b"one"]) == {b"two", b"three"}
        assert fs[b"test2"] == [b"xxx"]
        assert fs[b"six"] == [b"seven"]