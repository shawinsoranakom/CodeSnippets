def test_incomplete_read_error(self):
        error = IncompleteRead(4, 3, cause='test')
        assert isinstance(error, IncompleteRead)
        assert repr(error) == '<IncompleteRead: 4 bytes read, 3 more expected>'
        assert str(error) == error.msg == '4 bytes read, 3 more expected'
        assert error.partial == 4
        assert error.expected == 3
        assert error.cause == 'test'

        error = IncompleteRead(3)
        assert repr(error) == '<IncompleteRead: 3 bytes read>'
        assert str(error) == '3 bytes read'