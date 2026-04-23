def test_is_local() -> None:
    """Test local addresses."""
    assert network_util.is_local(ip_address("192.168.0.1"))
    assert network_util.is_local(ip_address("127.0.0.1"))
    assert network_util.is_local(ip_address("fd12:3456:789a:1::1"))
    assert network_util.is_local(ip_address("fe80::1234:5678:abcd"))
    assert network_util.is_local(ip_address("::ffff:192.168.0.1"))
    assert not network_util.is_local(ip_address("208.5.4.2"))
    assert not network_util.is_local(ip_address("198.51.100.1"))
    assert not network_util.is_local(ip_address("2001:DB8:FA1::1"))
    assert not network_util.is_local(ip_address("::ffff:208.5.4.2"))