def test_rabin_karp() -> None:
    """
    >>> test_rabin_karp()
    Success.
    """
    # Test 1)
    pattern = "abc1abc12"
    text1 = "alskfjaldsabc1abc1abc12k23adsfabcabc"
    text2 = "alskfjaldsk23adsfabcabc"
    assert rabin_karp(pattern, text1)
    assert not rabin_karp(pattern, text2)

    # Test 2)
    pattern = "ABABX"
    text = "ABABZABABYABABX"
    assert rabin_karp(pattern, text)

    # Test 3)
    pattern = "AAAB"
    text = "ABAAAAAB"
    assert rabin_karp(pattern, text)

    # Test 4)
    pattern = "abcdabcy"
    text = "abcxabcdabxabcdabcdabcy"
    assert rabin_karp(pattern, text)

    # Test 5)
    pattern = "Lü"
    text = "Lüsai"
    assert rabin_karp(pattern, text)
    pattern = "Lue"
    assert not rabin_karp(pattern, text)
    print("Success.")