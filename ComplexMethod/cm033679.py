def load_completion[TCompletionConfig: CompletionConfig](name: str, completion_type: t.Type[TCompletionConfig]) -> dict[str, TCompletionConfig]:
    """Load the named completion entries, returning them in dictionary form using the specified completion type."""
    lines = read_lines_without_comments(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'completion', '%s.txt' % name), remove_blank_lines=True)

    if data_context().content.collection:
        context = 'collection'
    else:
        context = 'ansible-core'

    items = {name: data for name, data in [parse_completion_entry(line) for line in lines] if data.get('context', context) == context}
    aliases: dict[tuple[str, str], dict[str, str]] = {}
    aliases_seen: set[str] = set()

    for item_name, item in items.items():
        item.pop('context', None)
        item.pop('placeholder', None)

        if alias := item.pop('alias', None):
            for aliased_name in alias.split(','):
                if aliased_name in aliases_seen:
                    raise InternalError(f"Duplicate alias {aliased_name!r} found for {name!r} completion.")

                aliases_seen.add(aliased_name)
                aliases[(aliased_name, item_name)] = item

    completion = {name: completion_type(name=name, **data) for name, data in items.items()}
    completion |= {an[0]: completion_type(name=an[1], **data) for an, data in aliases.items()}
    completion = dict(sorted(completion.items(), key=lambda entry: entry[1].sort_key))

    return completion