def doc_schema(module_name, for_collection=False, deprecated_module=False, plugin_type='module'):

    if module_name.startswith('_') and not for_collection:
        module_name = module_name[1:]
        deprecated_module = True
    doc_schema_dict = {
        Required('module' if plugin_type == 'module' else 'name'): module_name,
        Required('short_description'): doc_string,
        Required('description'): doc_string_or_strings,
        'notes': Any(None, [doc_string]),
        'seealso': Any(None, seealso_schema),
        'requirements': [doc_string],
        'todo': Any(None, doc_string_or_strings),
        'options': Any(None, *list_dict_option_schema(for_collection, plugin_type)),
        'extends_documentation_fragment': Any(list_string_types, str),
        'version_added_collection': collection_name,
    }
    if plugin_type == 'module':
        doc_schema_dict[Required('author')] = All(Any(None, list_string_types, str), author)
    else:
        # author is optional for plugins (for now)
        doc_schema_dict['author'] = All(Any(None, list_string_types, str), author)
    if plugin_type == 'callback':
        doc_schema_dict[Required('type')] = Any('aggregate', 'notification', 'stdout')

    if for_collection:
        # Optional
        doc_schema_dict['version_added'] = version(for_collection=True)
    else:
        doc_schema_dict[Required('version_added')] = version(for_collection=False)

    if deprecated_module:
        deprecation_required_scheme = {
            Required('deprecated'): Any(deprecation_schema(for_collection=for_collection)),
        }

        doc_schema_dict.update(deprecation_required_scheme)

    def add_default_attributes(more=None):
        schema = {
            'description': doc_string_or_strings,
            'details': doc_string_or_strings,
            'support': str,
            'version_added_collection': str,
            'version_added': str,
        }
        if more:
            schema.update(more)
        return schema

    doc_schema_dict['attributes'] = Schema(
        All(
            Schema({
                str: {
                    Required('description'): doc_string_or_strings,
                    Required('support'): Any('full', 'partial', 'none', 'N/A'),
                    'details': doc_string_or_strings,
                    'version_added_collection': collection_name,
                    'version_added': version(for_collection=for_collection),
                },
            }, extra=ALLOW_EXTRA),
            partial(version_added, error_code='attribute-invalid-version-added', accept_historical=False),
            Schema({
                str: add_default_attributes(),
                'action_group': add_default_attributes({
                    Required('membership'): list_string_types,
                }),
                'platform': add_default_attributes({
                    Required('platforms'): Any(list_string_types, str)
                }),
            }, extra=PREVENT_EXTRA),
        )
    )
    return Schema(
        All(
            Schema(
                doc_schema_dict,
                extra=PREVENT_EXTRA
            ),
            partial(version_added, error_code='module-invalid-version-added', accept_historical=not for_collection),
        )
    )