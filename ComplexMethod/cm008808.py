def find_element(*, tag=None, id=None, cls=None, attr=None, value=None, html=False, regex=False):
    # deliberately using `id=` and `cls=` for ease of readability
    assert tag or id or cls or (attr and value), 'One of tag, id, cls or (attr AND value) is required'
    ANY_TAG = r'[\w:.-]+'

    if attr and value:
        assert not cls, 'Cannot match both attr and cls'
        assert not id, 'Cannot match both attr and id'
        func = get_element_html_by_attribute if html else get_element_by_attribute
        return functools.partial(func, attr, value, tag=tag or ANY_TAG, escape_value=not regex)

    elif cls:
        assert not id, 'Cannot match both cls and id'
        assert tag is None, 'Cannot match both cls and tag'
        assert not regex, 'Cannot use regex with cls'
        func = get_element_html_by_class if html else get_element_by_class
        return functools.partial(func, cls)

    elif id:
        func = get_element_html_by_id if html else get_element_by_id
        return functools.partial(func, id, tag=tag or ANY_TAG, escape_value=not regex)

    index = int(bool(html))
    return lambda html: get_element_text_and_html_by_tag(tag, html)[index]