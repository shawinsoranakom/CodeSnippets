def _load_plugin_filter():
    filters = _PLUGIN_FILTERS
    user_set = False
    if C.PLUGIN_FILTERS_CFG is None:
        filter_cfg = '/etc/ansible/plugin_filters.yml'
    else:
        filter_cfg = C.PLUGIN_FILTERS_CFG
        user_set = True

    if os.path.exists(filter_cfg):
        with open(filter_cfg, 'rb') as f:
            try:
                filter_data = yaml.load(f, Loader=AnsibleInstrumentedLoader)
            except Exception as e:
                display.warning(u'The plugin filter file, {0} was not parsable.'
                                u' Skipping: {1}'.format(filter_cfg, to_text(e)))
                return filters

        try:
            version = filter_data['filter_version']
        except KeyError:
            display.warning(u'The plugin filter file, {0} was invalid.'
                            u' Skipping.'.format(filter_cfg))
            return filters

        # Try to convert for people specifying version as a float instead of string
        version = to_text(version)
        version = version.strip()

        # Modules and action plugins share the same reject list since the difference between the
        # two isn't visible to the users
        if version == u'1.0':
            try:
                filters['ansible.modules'] = frozenset(filter_data['module_rejectlist'])
            except TypeError:
                display.warning(u'Unable to parse the plugin filter file {0} as'
                                u' module_rejectlist is not a list.'
                                u' Skipping.'.format(filter_cfg))
                return filters
            filters['ansible.plugins.action'] = filters['ansible.modules']
        else:
            display.warning(u'The plugin filter file, {0} was a version not recognized by this'
                            u' version of Ansible. Skipping.'.format(filter_cfg))
    else:
        if user_set:
            display.warning(u'The plugin filter file, {0} does not exist.'
                            u' Skipping.'.format(filter_cfg))

    # Special case: the stat module as Ansible can run very few things if stat is rejected
    if 'stat' in filters['ansible.modules']:
        raise AnsibleError('The stat module was specified in the module reject list file, {0}, but'
                           ' Ansible will not function without the stat module.  Please remove stat'
                           ' from the reject list.'.format(to_native(filter_cfg)))
    return filters