def test_parse_instance_minimal(self, parser: XBRLParser):
        """Minimal instance doc with one context, one unit, one fact."""
        xml_str = (
            '<?xml version="1.0"?>'
            "<xbrli:xbrl "
            '  xmlns:xbrli="http://www.xbrl.org/2003/instance"'
            '  xmlns:us-gaap="http://fasb.org/us-gaap/2024"'
            '  xmlns:link="http://www.xbrl.org/2003/linkbase"'
            '  xmlns:xlink="http://www.w3.org/1999/xlink">'
            '  <xbrli:context id="ctx1">'
            "    <xbrli:entity>"
            '      <xbrli:identifier scheme="http://www.sec.gov/CIK">0000320193</xbrli:identifier>'
            "    </xbrli:entity>"
            "    <xbrli:period>"
            "      <xbrli:instant>2024-09-28</xbrli:instant>"
            "    </xbrli:period>"
            "  </xbrli:context>"
            '  <xbrli:unit id="usd">'
            "    <xbrli:measure>iso4217:USD</xbrli:measure>"
            "  </xbrli:unit>"
            '  <us-gaap:Assets contextRef="ctx1" unitRef="usd" decimals="-6">364980000000</us-gaap:Assets>'
            "</xbrli:xbrl>"
        )
        content = BytesIO(xml_str.encode("utf-8"))
        contexts, units, facts = parser.parse_instance(content)

        assert "ctx1" in contexts
        assert contexts["ctx1"]["entity"] == "0000320193"
        assert contexts["ctx1"]["period_type"] == "instant"
        assert contexts["ctx1"]["end"] == "2024-09-28"
        assert units["usd"] == "iso4217:USD"
        assert "us-gaap_Assets" in facts
        fact = facts["us-gaap_Assets"][0]
        assert fact["value"] == "364980000000"
        assert fact["unit"] == "iso4217:USD"
        assert fact["decimals"] == "-6"
        assert fact["entity"] == "0000320193"
        assert fact["period_type"] == "instant"