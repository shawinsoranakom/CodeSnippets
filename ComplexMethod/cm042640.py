def test_basics(self):
        h = Headers({"Content-Type": "text/html", "Content-Length": 1234})
        assert h["Content-Type"]
        assert h["Content-Length"]

        with pytest.raises(KeyError):
            h["Accept"]
        assert h.get("Accept") is None
        assert h.getlist("Accept") == []

        assert h.get("Accept", "*/*") == b"*/*"
        assert h.getlist("Accept", "*/*") == [b"*/*"]
        assert h.getlist("Accept", ["text/html", "images/jpeg"]) == [
            b"text/html",
            b"images/jpeg",
        ]