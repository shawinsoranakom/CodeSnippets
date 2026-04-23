def test_headers(self, handler):
        with handler(headers=std_headers) as rh:
            # Ensure curl-impersonate overrides our standard headers (usually added
            res = validate_and_send(
                rh, Request(f'http://127.0.0.1:{self.http_port}/headers', extensions={
                    'impersonate': ImpersonateTarget('safari')}, headers={'x-custom': 'test', 'sec-fetch-mode': 'custom'})).read().decode().lower()

            assert std_headers['user-agent'].lower() not in res
            assert std_headers['accept-language'].lower() not in res
            assert std_headers['sec-fetch-mode'].lower() not in res
            # other than UA, custom headers that differ from std_headers should be kept
            assert 'sec-fetch-mode: custom' in res
            assert 'x-custom: test' in res
            # but when not impersonating don't remove std_headers
            res = validate_and_send(
                rh, Request(f'http://127.0.0.1:{self.http_port}/headers', headers={'x-custom': 'test'})).read().decode().lower()
            # std_headers should be present
            for k, v in std_headers.items():
                assert f'{k}: {v}'.lower() in res