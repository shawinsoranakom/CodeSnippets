def test_compat_request(self):
        with FakeRHYDL() as ydl:
            assert ydl.urlopen('test://')
            urllib_req = urllib.request.Request('http://foo.bar', data=b'test', method='PUT', headers={'X-Test': '1'})
            urllib_req.add_unredirected_header('Cookie', 'bob=bob')
            urllib_req.timeout = 2
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', category=DeprecationWarning)
                req = ydl.urlopen(urllib_req).request
                assert req.url == urllib_req.get_full_url()
                assert req.data == urllib_req.data
                assert req.method == urllib_req.get_method()
                assert 'X-Test' in req.headers
                assert 'Cookie' in req.headers
                assert req.extensions.get('timeout') == 2

            with pytest.raises(AssertionError):
                ydl.urlopen(None)