def test_response_reader(self, handler):
        class FakeResponse:
            def __init__(self, raise_error=False):
                self.raise_error = raise_error
                self.closed = False

            def iter_content(self):
                yield b'foo'
                yield b'bar'
                yield b'z'
                if self.raise_error:
                    raise Exception('test')

            def close(self):
                self.closed = True

        from yt_dlp.networking._curlcffi import CurlCFFIResponseReader

        res = CurlCFFIResponseReader(FakeResponse())
        assert res.readable
        assert res.bytes_read == 0
        assert res.read(1) == b'f'
        assert res.bytes_read == 3
        assert res._buffer == b'oo'

        assert res.read(2) == b'oo'
        assert res.bytes_read == 3
        assert res._buffer == b''

        assert res.read(2) == b'ba'
        assert res.bytes_read == 6
        assert res._buffer == b'r'

        assert res.read(3) == b'rz'
        assert res.bytes_read == 7
        assert res._buffer == b''
        assert res.closed
        assert res._response.closed

        # should handle no size param
        res2 = CurlCFFIResponseReader(FakeResponse())
        assert res2.read() == b'foobarz'
        assert res2.bytes_read == 7
        assert res2._buffer == b''
        assert res2.closed

        # should close on an exception
        res3 = CurlCFFIResponseReader(FakeResponse(raise_error=True))
        with pytest.raises(Exception, match='test'):
            res3.read()
        assert res3._buffer == b''
        assert res3.bytes_read == 7
        assert res3.closed

        # buffer should be cleared on close
        res4 = CurlCFFIResponseReader(FakeResponse())
        res4.read(2)
        assert res4._buffer == b'o'
        res4.close()
        assert res4.closed
        assert res4._buffer == b''