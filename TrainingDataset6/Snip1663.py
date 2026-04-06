def test_parse(argv, result):
    assert vars(Parser().parse(argv)) == result