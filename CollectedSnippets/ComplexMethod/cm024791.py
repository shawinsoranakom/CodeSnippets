def test_is_loopback() -> None:
    """Test loopback addresses."""
    assert network_util.is_loopback(ip_address("127.0.0.2"))
    assert network_util.is_loopback(ip_address("127.0.0.1"))
    assert network_util.is_loopback(ip_address("::1"))
    assert network_util.is_loopback(ip_address("::ffff:127.0.0.0"))
    assert network_util.is_loopback(ip_address("0:0:0:0:0:0:0:1"))
    assert network_util.is_loopback(ip_address("0:0:0:0:0:ffff:7f00:1"))
    assert not network_util.is_loopback(ip_address("104.26.5.238"))
    assert not network_util.is_loopback(ip_address("2600:1404:400:1a4::356e"))