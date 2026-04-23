def test_is_comma_limited_list():
    assert is_comma_delimited_list("foo")
    assert is_comma_delimited_list("foo,bar")
    assert is_comma_delimited_list("foo, bar")
    assert is_comma_delimited_list("foo , bar")
    assert is_comma_delimited_list(" foo,bar ")

    assert is_comma_delimited_list("s3,cognito-idp")

    assert not is_comma_delimited_list("foo, bar baz")
    assert not is_comma_delimited_list("foo,")
    assert not is_comma_delimited_list("")