def untag(value: _T, *tag_types: t.Type[AnsibleDatatagBase]) -> _T:
        """
        If tags matching any of `tag_types` are present on `value`, return a copy with those tags removed.
        If no `tag_types` are specified and the object has tags, return a copy with all tags removed.
        Otherwise, the original `value` is returned.
        """
        tag_set = AnsibleTagHelper.tags(value)

        if not tag_set:
            return value

        if tag_types:
            tags_mapping = _AnsibleTagsMapping((type(tag), tag) for tag in tag_set if type(tag) not in tag_types)  # pylint: disable=unidiomatic-typecheck

            if len(tags_mapping) == len(tag_set):
                return value  # if no tags were removed, return the original instance
        else:
            tags_mapping = None

        if not tags_mapping:
            if t.cast(AnsibleTaggedObject, value)._empty_tags_as_native:
                return t.cast(AnsibleTaggedObject, value)._native_copy()

            tags_mapping = _EMPTY_INTERNAL_TAGS_MAPPING

        tagged_type = AnsibleTaggedObject._get_tagged_type(type(value))

        return t.cast(_T, tagged_type._instance_factory(value, tags_mapping))