def test_strip_accents():
    # check some classical latin accentuated symbols
    a = "àáâãäåçèéêë"
    expected = "aaaaaaceeee"
    assert strip_accents_unicode(a) == expected

    a = "ìíîïñòóôõöùúûüý"
    expected = "iiiinooooouuuuy"
    assert strip_accents_unicode(a) == expected

    # check some arabic
    a = "\u0625"  # alef with a hamza below: إ
    expected = "\u0627"  # simple alef: ا
    assert strip_accents_unicode(a) == expected

    # mix letters accentuated and not
    a = "this is à test"
    expected = "this is a test"
    assert strip_accents_unicode(a) == expected

    # strings that are already decomposed
    a = "o\u0308"  # o with diaeresis
    expected = "o"
    assert strip_accents_unicode(a) == expected

    # combining marks by themselves
    a = "\u0300\u0301\u0302\u0303"
    expected = ""
    assert strip_accents_unicode(a) == expected

    # Multiple combining marks on one character
    a = "o\u0308\u0304"
    expected = "o"
    assert strip_accents_unicode(a) == expected