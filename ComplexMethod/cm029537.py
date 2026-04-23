def test_wildcard_username_expansion():
    assert sherlock.check_for_parameter('test{?}test') is True
    assert sherlock.check_for_parameter('test{.}test') is False
    assert sherlock.check_for_parameter('test{}test') is False
    assert sherlock.check_for_parameter('testtest') is False
    assert sherlock.check_for_parameter('test{?test') is False
    assert sherlock.check_for_parameter('test?}test') is False
    assert sherlock.multiple_usernames('test{?}test') == ["test_test" , "test-test" , "test.test"]