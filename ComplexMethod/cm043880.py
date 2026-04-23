def test_parse_query_variants(imf_metadata):
    assert imf_metadata._parse_query("gold") == [["gold"]]
    assert imf_metadata._parse_query('"central bank"') == [["central bank"]]
    assert imf_metadata._parse_query("gold + reserves") == [["gold", "reserves"]]
    assert imf_metadata._parse_query("gold | reserves") == [["gold"], ["reserves"]]
    assert imf_metadata._parse_query('gold + reserves | "central bank"') == [
        ["gold", "reserves"],
        ["central bank"],
    ]
    assert imf_metadata._parse_query("") == []
    assert imf_metadata._parse_query("   ") == []