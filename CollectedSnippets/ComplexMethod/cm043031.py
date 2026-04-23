def test_proxy_config_from_env_multiple_proxies(self):
        """Test loading multiple proxies from environment variable."""
        proxy_list = [
            "192.168.1.1:8080:user1:pass1",
            "192.168.1.2:8080:user2:pass2",
            "10.0.0.1:3128"  # No auth
        ]
        proxy_str = ",".join(proxy_list)

        with patch.dict(os.environ, {'TEST_PROXIES': proxy_str}):
            proxies = ProxyConfig.from_env('TEST_PROXIES')
            assert len(proxies) == 3

            # Check first proxy
            assert proxies[0].ip == "192.168.1.1"
            assert proxies[0].username == "user1"
            assert proxies[0].password == "pass1"

            # Check second proxy
            assert proxies[1].ip == "192.168.1.2"
            assert proxies[1].username == "user2"
            assert proxies[1].password == "pass2"

            # Check third proxy (no auth)
            assert proxies[2].ip == "10.0.0.1"
            assert proxies[2].username is None
            assert proxies[2].password is None