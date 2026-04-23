def test_read(self, handler):
        with handler() as rh:
            res = validate_and_send(
                rh, Request(f'http://127.0.0.1:{self.http_port}/headers'))
            assert res.readable()
            assert res.read(1) == b'H'
            # Ensure we don't close the adaptor yet
            assert not res.closed
            assert res.read(3) == b'ost'
            assert res.read().decode().endswith('\n\n')
            assert res.read() == b''
            # Should auto-close and mark the response adaptor as closed
            assert res.closed