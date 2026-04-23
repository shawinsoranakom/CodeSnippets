def test_data_uri_partial_read_greater_than_response_then_full_read(self, handler):
        with handler() as rh:
            res = validate_and_send(rh, Request('data:text/plain,hello%20world'))
            assert res.read(512) == b'hello world'
            # Response and its underlying file object should already be closed now
            assert res.fp.closed
            assert res.closed
            assert res.read(0) == b''
            assert res.read() == b''
            assert res.fp.closed
            assert res.closed