def test_tag_builtins():
    values = [123, 123.45, 'a string value', tuple([1, 2, 3]), [1, 2, 3], {1, 2, 3}, dict(one=1, two=2)]

    for original_val in values:
        tagged_val = TrustedAsTemplate().tag(original_val)
        zero_tagged_val = AnsibleTagHelper.tag(original_val, [])  # should return original value, not an empty tagged obj

        assert original_val == tagged_val  # equality should pass
        assert not TrustedAsTemplate.is_tagged_on(original_val)  # immutable original value via bool check
        assert TrustedAsTemplate.get_tag(original_val) is None  # immutable original value via get_tag
        assert not AnsibleTagHelper.tags(original_val)  # immutable original value via tags

        assert TrustedAsTemplate.is_tagged_on(tagged_val)
        assert TrustedAsTemplate.get_tag(tagged_val) is TrustedAsTemplate()  # singleton tag type, should be reference-equal
        assert original_val is zero_tagged_val  # original value should reference-equal the zero-tagged value

        origin = Origin(path="/foo", line_num=12, col_num=34)

        multi_tagged_val = origin.tag(tagged_val)
        assert tagged_val is not multi_tagged_val
        assert TrustedAsTemplate.is_tagged_on(multi_tagged_val)
        assert Origin.is_tagged_on(multi_tagged_val)
        assert TrustedAsTemplate.get_tag(multi_tagged_val) is TrustedAsTemplate()  # singleton tag type, should be reference-equal
        assert Origin.get_tag(multi_tagged_val) is origin