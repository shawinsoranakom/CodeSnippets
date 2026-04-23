def test_untag(self, value: object) -> None:
        """Ensure tagging and then untagging a taggable instance returns new instances as appropriate, with the correct tags and type."""
        tagged_instance = ExampleSingletonTag().tag(AnotherExampleSingletonTag().tag(value))

        tags_unchanged = Deprecated.untag(tagged_instance)  # not tagged with this value, nothing to do

        assert tags_unchanged is tagged_instance

        one_less_tag = AnotherExampleSingletonTag.untag(tagged_instance)

        assert one_less_tag is not tagged_instance
        assert type(one_less_tag) is type(tagged_instance)  # pylint: disable=unidiomatic-typecheck
        assert AnsibleTagHelper.tags(one_less_tag) == frozenset((ExampleSingletonTag(),))

        no_tags = ExampleSingletonTag.untag(one_less_tag)

        assert no_tags is not one_less_tag
        assert type(no_tags) is type(value)
        assert AnsibleTagHelper.tags(no_tags) is _empty_frozenset

        still_no_tags = ExampleSingletonTag.untag(no_tags)

        assert still_no_tags is no_tags