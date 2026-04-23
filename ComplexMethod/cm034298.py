def get_deprecation_message_with_plugin_info(
    *,
    msg: str,
    version: str | None,
    removed: bool = False,
    date: str | None,
    deprecator: _messages.PluginInfo | None,
) -> str:
    """Internal use only. Return a deprecation message and help text for display."""
    # DTFIX-FUTURE: the logic for omitting date/version doesn't apply to the payload, so it shows up in vars in some cases when it should not

    if removed:
        removal_fragment = 'This feature was removed'
    else:
        removal_fragment = 'This feature will be removed'

    if not deprecator or not deprecator.type:
        # indeterminate has no resolved_name or type
        # collections have a resolved_name but no type
        collection = deprecator.resolved_name if deprecator else None
        plugin_fragment = ''
    elif deprecator.resolved_name == 'ansible.builtin':
        # core deprecations from base classes (the API) have no plugin name, only 'ansible.builtin'
        plugin_type_name = str(deprecator.type) if deprecator.type is _messages.PluginType.MODULE else f'{deprecator.type} plugin'

        collection = deprecator.resolved_name
        plugin_fragment = f'the {plugin_type_name} API'
    else:
        parts = deprecator.resolved_name.split('.')
        plugin_name = parts[-1]
        plugin_type_name = str(deprecator.type) if deprecator.type is _messages.PluginType.MODULE else f'{deprecator.type} plugin'

        collection = '.'.join(parts[:2]) if len(parts) > 2 else None
        plugin_fragment = f'{plugin_type_name} {plugin_name!r}'

    if collection and plugin_fragment:
        plugin_fragment += ' in'

    if collection == 'ansible.builtin':
        collection_fragment = 'ansible-core'
    elif collection:
        collection_fragment = f'collection {collection!r}'
    else:
        collection_fragment = ''

    if not collection:
        when_fragment = 'in the future' if not removed else ''
    elif date:
        when_fragment = f'in a release after {date}'
    elif version:
        when_fragment = f'version {version}'
    else:
        when_fragment = 'in a future release' if not removed else ''

    if plugin_fragment or collection_fragment:
        from_fragment = 'from'
    else:
        from_fragment = ''

    deprecation_msg = ' '.join(f for f in [removal_fragment, from_fragment, plugin_fragment, collection_fragment, when_fragment] if f) + '.'

    return join_sentences(msg, deprecation_msg)