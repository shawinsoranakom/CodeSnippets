def find_elements(*, tag=None, cls=None, attr=None, value=None, html=False, regex=False):
    # deliberately using `cls=` for ease of readability
    assert cls or (attr and value), 'One of cls or (attr AND value) is required'

    if attr and value:
        assert not cls, 'Cannot match both attr and cls'
        func = get_elements_html_by_attribute if html else get_elements_by_attribute
        return functools.partial(func, attr, value, tag=tag or r'[\w:.-]+', escape_value=not regex)

    assert not tag, 'Cannot match both cls and tag'
    assert not regex, 'Cannot use regex with cls'
    func = get_elements_html_by_class if html else get_elements_by_class
    return functools.partial(func, cls)