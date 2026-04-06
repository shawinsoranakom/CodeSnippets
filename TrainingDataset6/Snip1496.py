def test_get_new_command(sed_unterminated_s):
    assert (get_new_command(Command('sed -e s/foo/bar', sed_unterminated_s))
            == 'sed -e s/foo/bar/')
    assert (get_new_command(Command('sed -es/foo/bar', sed_unterminated_s))
            == 'sed -es/foo/bar/')
    assert (get_new_command(Command(r"sed -e 's/\/foo/bar'", sed_unterminated_s))
            == r"sed -e 's/\/foo/bar/'")
    assert (get_new_command(Command(r"sed -e s/foo/bar -es/baz/quz", sed_unterminated_s))
            == r"sed -e s/foo/bar/ -es/baz/quz/")