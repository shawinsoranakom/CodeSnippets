def test_simple_selection(self):
        """Simple selector tests"""
        body = b"<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        response = TextResponse(url="http://example.com", body=body, encoding="utf-8")
        sel = Selector(response)

        xl = sel.xpath("//input")
        assert len(xl) == 2
        for x in xl:
            assert isinstance(x, Selector)

        assert sel.xpath("//input").getall() == [x.get() for x in sel.xpath("//input")]
        assert [x.get() for x in sel.xpath("//input[@name='a']/@name")] == ["a"]
        assert [
            x.get()
            for x in sel.xpath(
                "number(concat(//input[@name='a']/@value, //input[@name='b']/@value))"
            )
        ] == ["12.0"]
        assert sel.xpath("concat('xpath', 'rules')").getall() == ["xpathrules"]
        assert [
            x.get()
            for x in sel.xpath(
                "concat(//input[@name='a']/@value, //input[@name='b']/@value)"
            )
        ] == ["12"]