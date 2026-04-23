def tag(value: _T, tags: t.Union[AnsibleDatatagBase, t.Iterable[AnsibleDatatagBase]], *, value_type: t.Optional[type] = None) -> _T:
        """
        Return a copy of `value`, with `tags` applied, overwriting any existing tags of the same types.
        If `value` is an ignored type, or `tags` is empty, the original `value` will be returned.
        If `value` is not taggable, a `NotTaggableError` exception will be raised.
        If `value_type` was given, that type will be returned instead.
        """
        if value_type is None:
            value_type_specified = False
            value_type = type(value)
        else:
            value_type_specified = True

        # if no tags to apply, just return what we got
        # NB: this only works because the untaggable types are singletons (and thus direct type comparison works)
        if not tags or value_type in _untaggable_types:
            if value_type_specified:
                return value_type(value)

            return value

        tag_list: list[AnsibleDatatagBase]

        # noinspection PyProtectedMember
        if type(tags) in _known_tag_types:
            tag_list = [tags]  # type: ignore[list-item]
        else:
            tag_list = list(tags)  # type: ignore[arg-type]

            for idx, tag in enumerate(tag_list):
                # noinspection PyProtectedMember
                if type(tag) not in _known_tag_types:
                    # noinspection PyProtectedMember
                    raise TypeError(f'tags[{idx}] of type {type(tag)} is not one of {_known_tag_types}')

        existing_internal_tags_mapping = _try_get_internal_tags_mapping(value)

        if existing_internal_tags_mapping is not _EMPTY_INTERNAL_TAGS_MAPPING:
            # include the existing tags first so new tags of the same type will overwrite
            tag_list = list(chain(existing_internal_tags_mapping.values(), tag_list))

        tags_mapping = _AnsibleTagsMapping((type(tag), tag) for tag in tag_list)
        tagged_type = AnsibleTaggedObject._get_tagged_type(value_type)

        return t.cast(_T, tagged_type._instance_factory(value, tags_mapping))