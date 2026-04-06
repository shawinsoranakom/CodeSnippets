def test_match(sed_unterminated_s):
    assert match(Command('sed -e s/foo/bar', sed_unterminated_s))
    assert match(Command('sed -es/foo/bar', sed_unterminated_s))
    assert match(Command('sed -e s/foo/bar -e s/baz/quz', sed_unterminated_s))
    assert not match(Command('sed -e s/foo/bar', ''))
    assert not match(Command('sed -es/foo/bar', ''))
    assert not match(Command('sed -e s/foo/bar -e s/baz/quz', ''))