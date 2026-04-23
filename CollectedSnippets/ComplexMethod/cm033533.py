def test_helper_untag():
    """Validate the behavior of the `AnsibleTagHelper.untag` method."""
    value = AnsibleTagHelper.tag("value", tags=[ExampleSingletonTag(), ExampleTagWithContent(content_str="blah")])
    assert len(AnsibleTagHelper.tag_types(value)) == 2

    less_est = AnsibleTagHelper.untag(value, ExampleSingletonTag)
    assert AnsibleTagHelper.tag_types(less_est) == {ExampleTagWithContent}

    no_tags_explicit = AnsibleTagHelper.untag(value, ExampleSingletonTag, ExampleTagWithContent)
    assert type(no_tags_explicit) is str  # pylint: disable=unidiomatic-typecheck

    no_tags_implicit = AnsibleTagHelper.untag(value)
    assert type(no_tags_implicit) is str  # pylint: disable=unidiomatic-typecheck

    untagged_value = "not a tagged value"
    assert AnsibleTagHelper.untag(untagged_value) is untagged_value

    tagged_empty_tags_ok_value = ExampleSingletonTag().tag(NonNativeTaggedType("blah"))
    untagged_empty_tags_ok_value = AnsibleTagHelper.untag(tagged_empty_tags_ok_value)
    assert type(untagged_empty_tags_ok_value) is NonNativeTaggedType  # pylint: disable=unidiomatic-typecheck
    assert not AnsibleTagHelper.tags(untagged_empty_tags_ok_value)