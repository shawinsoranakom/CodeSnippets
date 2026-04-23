def test_build_handler_params(self):
        with FakeYDL({
            'http_headers': {'test': 'testtest'},
            'socket_timeout': 2,
            'proxy': 'http://127.0.0.1:8080',
            'source_address': '127.0.0.45',
            'debug_printtraffic': True,
            'compat_opts': ['no-certifi'],
            'nocheckcertificate': True,
            'legacyserverconnect': True,
        }) as ydl:
            rh = self.build_handler(ydl)
            assert rh.headers.get('test') == 'testtest'
            assert 'Accept' in rh.headers  # ensure std_headers are still there
            assert rh.timeout == 2
            assert rh.proxies.get('all') == 'http://127.0.0.1:8080'
            assert rh.source_address == '127.0.0.45'
            assert rh.verbose is True
            assert rh.prefer_system_certs is True
            assert rh.verify is False
            assert rh.legacy_ssl_support is True