def test_encoding(self):
        r1 = self.response_class(
            "http://www.example.com",
            body=b"\xc2\xa3",
            headers={"Content-type": ["text/html; charset=utf-8"]},
        )
        r2 = self.response_class(
            "http://www.example.com", encoding="utf-8", body="\xa3"
        )
        r3 = self.response_class(
            "http://www.example.com",
            body=b"\xa3",
            headers={"Content-type": ["text/html; charset=iso-8859-1"]},
        )
        r4 = self.response_class("http://www.example.com", body=b"\xa2\xa3")
        r5 = self.response_class(
            "http://www.example.com",
            body=b"\xc2\xa3",
            headers={"Content-type": ["text/html; charset=None"]},
        )
        r6 = self.response_class(
            "http://www.example.com",
            body=b"\xa8D",
            headers={"Content-type": ["text/html; charset=gb2312"]},
        )
        r7 = self.response_class(
            "http://www.example.com",
            body=b"\xa8D",
            headers={"Content-type": ["text/html; charset=gbk"]},
        )
        r8 = self.response_class(
            "http://www.example.com",
            body=codecs.BOM_UTF8 + b"\xc2\xa3",
            headers={"Content-type": ["text/html; charset=cp1251"]},
        )
        r9 = self.response_class(
            "http://www.example.com",
            body=b"\x80",
            headers={
                "Content-type": [b"application/x-download; filename=\x80dummy.txt"]
            },
        )

        assert r1._headers_encoding() == "utf-8"
        assert r2._headers_encoding() is None
        assert r2._declared_encoding() == "utf-8"
        self._assert_response_encoding(r2, "utf-8")
        assert r3._headers_encoding() == "cp1252"
        assert r3._declared_encoding() == "cp1252"
        assert r4._headers_encoding() is None
        assert r5._headers_encoding() is None
        assert r8._headers_encoding() == "cp1251"
        assert r9._headers_encoding() is None
        assert r8._declared_encoding() == "utf-8"
        assert r9._declared_encoding() is None
        self._assert_response_encoding(r5, "utf-8")
        self._assert_response_encoding(r8, "utf-8")
        self._assert_response_encoding(r9, "cp1252")
        assert r4._body_inferred_encoding() is not None
        assert r4._body_inferred_encoding() != "ascii"
        self._assert_response_values(r1, "utf-8", "\xa3")
        self._assert_response_values(r2, "utf-8", "\xa3")
        self._assert_response_values(r3, "iso-8859-1", "\xa3")
        self._assert_response_values(r6, "gb18030", "\u2015")
        self._assert_response_values(r7, "gb18030", "\u2015")
        self._assert_response_values(r9, "cp1252", "€")

        # TextResponse (and subclasses) must be passed a encoding when instantiating with unicode bodies
        with pytest.raises(TypeError):
            self.response_class("http://www.example.com", body="\xa3")