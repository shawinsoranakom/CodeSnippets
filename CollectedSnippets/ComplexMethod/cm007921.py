def test_redirect(self, handler, redirect_status, method, expected):
        with handler() as rh:
            data = b'testdata' if method == 'POST' else None
            headers = {}
            if data is not None:
                headers['Content-Type'] = 'application/test'
            res = validate_and_send(
                rh, Request(f'http://127.0.0.1:{self.http_port}/redirect_{redirect_status}', method=method, data=data,
                            headers=headers))

            headers = b''
            data_recv = b''
            if data is not None:
                data_recv += res.read(len(data))
                if data_recv != data:
                    headers += data_recv
                    data_recv = b''

            headers += res.read()

            assert expected[0] == data_recv.decode()
            assert expected[1] == res.headers.get('method')
            assert expected[2] == ('content-length' in headers.decode().lower())