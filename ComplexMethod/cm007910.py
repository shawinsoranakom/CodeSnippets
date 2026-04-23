def test_trim_str(self):
        with pytest.raises(TypeError):
            trim_str('positional')

        assert callable(trim_str(start='a'))
        assert trim_str(start='ab')('abc') == 'c'
        assert trim_str(end='bc')('abc') == 'a'
        assert trim_str(start='a', end='c')('abc') == 'b'
        assert trim_str(start='ab', end='c')('abc') == ''
        assert trim_str(start='a', end='bc')('abc') == ''
        assert trim_str(start='ab', end='bc')('abc') == ''
        assert trim_str(start='abc', end='abc')('abc') == ''
        assert trim_str(start='', end='')('abc') == 'abc'