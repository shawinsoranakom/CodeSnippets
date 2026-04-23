def test_pairwise_string_result_output_parser_parse() -> None:
    output_parser = PairwiseStringResultOutputParser()
    text = """I like pie better than cake.
[[A]]"""
    got = output_parser.parse(text)
    want = {
        "reasoning": text,
        "value": "A",
        "score": 1,
    }
    assert got.get("reasoning") == want["reasoning"]
    assert got.get("value") == want["value"]
    assert got.get("score") == want["score"]

    text = """I like cake better than pie.
[[B]]"""
    got = output_parser.parse(text)
    want = {
        "reasoning": text,
        "value": "B",
        "score": 0,
    }
    assert got.get("reasoning") == want["reasoning"]
    assert got.get("value") == want["value"]
    assert got.get("score") == want["score"]

    text = """I like cake and pie.
[[C]]"""
    got = output_parser.parse(text)
    want = {
        "reasoning": text,
        "value": None,
        "score": 0.5,
    }
    assert got.get("reasoning") == want["reasoning"]
    assert got.get("value") == want["value"]
    assert got.get("score") == want["score"]