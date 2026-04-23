def test_find_element(self):
        for improper_kwargs in [
            dict(attr='data-id'),
            dict(value='y'),
            dict(attr='data-id', value='y', cls='a'),
            dict(attr='data-id', value='y', id='x'),
            dict(cls='a', id='x'),
            dict(cls='a', tag='p'),
            dict(cls='[ab]', regex=True),
        ]:
            with pytest.raises(AssertionError):
                find_element(**improper_kwargs)(_TEST_HTML)

        assert find_element(cls='a')(_TEST_HTML) == '1'
        assert find_element(cls='a', html=True)(_TEST_HTML) == '<div class="a">1</div>'
        assert find_element(id='x')(_TEST_HTML) == '2'
        assert find_element(id='[ex]')(_TEST_HTML) is None
        assert find_element(id='[ex]', regex=True)(_TEST_HTML) == '2'
        assert find_element(id='x', html=True)(_TEST_HTML) == '<div class="a" id="x" custom="z">2</div>'
        assert find_element(attr='data-id', value='y')(_TEST_HTML) == '3'
        assert find_element(attr='data-id', value='y(?:es)?')(_TEST_HTML) is None
        assert find_element(attr='data-id', value='y(?:es)?', regex=True)(_TEST_HTML) == '3'
        assert find_element(
            attr='data-id', value='y', html=True)(_TEST_HTML) == '<div class="b" data-id="y" custom="z">3</div>'