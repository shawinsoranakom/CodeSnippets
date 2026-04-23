def test_text_normalizer():
    std = EnglishTextNormalizer()
    assert std("Let's") == "let us"
    assert std("he's like") == "he is like"
    assert std("she's been like") == "she has been like"
    assert std("10km") == "10 km"
    assert std("10mm") == "10 mm"
    assert std("RC232") == "rc 232"

    assert (
        std("Mr. Park visited Assoc. Prof. Kim Jr.")
        == "mister park visited associate professor kim junior"
    )