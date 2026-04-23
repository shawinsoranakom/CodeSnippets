def validate_metadata_file(path, is_ansible, check_deprecation_dates=False):
    """Validate explicit runtime metadata file"""
    try:
        with open(path, 'r', encoding='utf-8') as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (
            path,
            ex.context_mark.line + 1 if ex.context_mark else 0,
            ex.context_mark.column + 1 if ex.context_mark else 0,
            re.sub(r'\s+', ' ', str(ex)),
        ))
        return
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' % (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        return

    if is_ansible:
        current_version = get_ansible_version()
    else:
        current_version = get_collection_version()

    # Updates to schema MUST also be reflected in the documentation
    # ~https://docs.ansible.com/ansible-core/devel/dev_guide/developing_collections.html

    # plugin_routing schema

    avoid_additional_data = Schema(
        Any(
            {
                Required('removal_version'): any_value,
                'warning_text': any_value,
            },
            {
                Required('removal_date'): any_value,
                'warning_text': any_value,
            }
        ),
        extra=PREVENT_EXTRA
    )

    deprecation_schema = All(
        # The first schema validates the input, and the second makes sure no extra keys are specified
        Schema(
            {
                'removal_version': partial(removal_version, is_ansible=is_ansible,
                                           current_version=current_version),
                'removal_date': partial(isodate, check_deprecation_date=check_deprecation_dates),
                'warning_text': str,
            }
        ),
        avoid_additional_data
    )

    tombstoning_schema = All(
        # The first schema validates the input, and the second makes sure no extra keys are specified
        Schema(
            {
                'removal_version': partial(removal_version, is_ansible=is_ansible,
                                           current_version=current_version, is_tombstone=True),
                'removal_date': partial(isodate, is_tombstone=True),
                'warning_text': str,
            }
        ),
        avoid_additional_data
    )

    plugins_routing_common_schema = Schema({
        ('deprecation'): Any(deprecation_schema),
        ('tombstone'): Any(tombstoning_schema),
        ('redirect'): fqcr,
    }, extra=PREVENT_EXTRA)

    plugin_routing_schema = Any(plugins_routing_common_schema)

    # Adjusted schema for modules only
    plugin_routing_schema_modules = Any(
        plugins_routing_common_schema.extend({
            ('action_plugin'): fqcr}
        )
    )

    # Adjusted schema for module_utils
    plugin_routing_schema_mu = Any(
        plugins_routing_common_schema.extend({
            ('redirect'): str}
        ),
    )

    list_dict_plugin_routing_schema = [{str: plugin_routing_schema}]

    list_dict_plugin_routing_schema_mu = [{str: plugin_routing_schema_mu}]

    list_dict_plugin_routing_schema_modules = [{str: plugin_routing_schema_modules}]

    plugin_schema = Schema({
        ('action'): Any(None, *list_dict_plugin_routing_schema),
        ('become'): Any(None, *list_dict_plugin_routing_schema),
        ('cache'): Any(None, *list_dict_plugin_routing_schema),
        ('callback'): Any(None, *list_dict_plugin_routing_schema),
        ('cliconf'): Any(None, *list_dict_plugin_routing_schema),
        ('connection'): Any(None, *list_dict_plugin_routing_schema),
        ('doc_fragments'): Any(None, *list_dict_plugin_routing_schema),
        ('filter'): Any(None, *list_dict_plugin_routing_schema),
        ('httpapi'): Any(None, *list_dict_plugin_routing_schema),
        ('inventory'): Any(None, *list_dict_plugin_routing_schema),
        ('lookup'): Any(None, *list_dict_plugin_routing_schema),
        ('module_utils'): Any(None, *list_dict_plugin_routing_schema_mu),
        ('modules'): Any(None, *list_dict_plugin_routing_schema_modules),
        ('netconf'): Any(None, *list_dict_plugin_routing_schema),
        ('shell'): Any(None, *list_dict_plugin_routing_schema),
        ('strategy'): Any(None, *list_dict_plugin_routing_schema),
        ('terminal'): Any(None, *list_dict_plugin_routing_schema),
        ('test'): Any(None, *list_dict_plugin_routing_schema),
        ('vars'): Any(None, *list_dict_plugin_routing_schema),
    }, extra=PREVENT_EXTRA)

    # import_redirection schema

    import_redirection_schema = Any(
        Schema({
            ('redirect'): str,
            # import_redirect doesn't currently support deprecation
        }, extra=PREVENT_EXTRA)
    )

    list_dict_import_redirection_schema = [{str: import_redirection_schema}]

    # action_groups schema

    def at_most_one_dict(value):
        if isinstance(value, Sequence):
            if sum(1 for v in value if isinstance(v, Mapping)) > 1:
                raise Invalid('List must contain at most one dictionary')
        return value

    metadata_dict = Schema({
        Required('metadata'): Schema({
            'extend_group': [fqcr_or_shortname],
        }, extra=PREVENT_EXTRA)
    }, extra=PREVENT_EXTRA)
    action_group_schema = All([metadata_dict, fqcr_or_shortname], at_most_one_dict)
    list_dict_action_groups_schema = [{str: action_group_schema}]

    # top level schema

    schema = Schema({
        # All of these are optional
        ('plugin_routing'): Any(plugin_schema),
        ('import_redirection'): Any(None, *list_dict_import_redirection_schema),
        # requires_ansible: In the future we should validate this with SpecifierSet
        ('requires_ansible'): str,
        ('action_groups'): Any(*list_dict_action_groups_schema),
    }, extra=PREVENT_EXTRA)

    # Ensure schema is valid

    try:
        schema(routing)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line/column numbers
            print('%s:%d:%d: %s' % (path, 0, 0, humanize_error(routing, error)))