def _list_collection_plugins_with_info(
    ptype: str,
    collections: dict[str, bytes],
) -> dict[str, _PluginDocMetadata]:
    # TODO: update to use importlib.resources

    try:
        ploader = getattr(loader, '{0}_loader'.format(ptype))
    except AttributeError:
        raise AnsibleError(f"Cannot list plugins, incorrect plugin type {ptype!r} supplied.") from None

    builtin_jinja_plugins = {}
    plugin_paths = {}

    # get plugins for each collection
    for collection, path in collections.items():
        if collection == 'ansible.builtin':
            # dirs from ansible install, but not configured paths
            dirs = [d.path for d in ploader._get_paths_with_context() if d.internal]

            if ptype in ('filter', 'test'):
                builtin_jinja_plugins = get_jinja_builtin_plugin_descriptions(ptype)

        elif collection == 'ansible.legacy':
            # configured paths + search paths (should include basedirs/-M)
            dirs = [d.path for d in ploader._get_paths_with_context() if not d.internal]
            if context.CLIARGS.get('module_path', None):
                dirs.extend(context.CLIARGS['module_path'])
        else:
            # search path in this case is for locating collection itselfA
            b_ptype = to_bytes(C.COLLECTION_PTYPE_COMPAT.get(ptype, ptype))
            dirs = [to_native(os.path.join(path, b'plugins', b_ptype))]
            # acr = AnsibleCollectionRef.try_parse_fqcr(collection, ptype)
            # if acr:
            #     dirs = acr.subdirs
            # else:

            #     raise Exception('bad acr for %s, %s' % (collection, ptype))

        plugin_paths.update(_list_plugins_from_paths(ptype, dirs, collection, docs=True))

    plugins = {}
    if ptype in ('module',):
        # no 'invalid' tests for modules
        for plugin, plugin_path in plugin_paths.items():
            plugins[plugin] = _PluginDocMetadata(name=plugin, path=plugin_path)
    else:
        # detect invalid plugin candidates AND add loaded object to return data
        for plugin, plugin_path in plugin_paths.items():
            pobj = None
            try:
                pobj = ploader.get(plugin, class_only=True)
            except Exception as e:
                display.vvv("The '{0}' {1} plugin could not be loaded from '{2}': {3}".format(plugin, ptype, plugin_path, to_native(e)))

            plugins[plugin] = _PluginDocMetadata(
                name=plugin,
                path=plugin_path,
                plugin_obj=pobj,
                jinja_builtin_short_description=builtin_jinja_plugins.get(plugin),
            )

        # Add in any builtin Jinja2 plugins that have not been shadowed in Ansible.
        plugins.update(
            (plugin_name, _PluginDocMetadata(name=plugin_name, jinja_builtin_short_description=plugin_description))
            for plugin_name, plugin_description in builtin_jinja_plugins.items() if plugin_name not in plugins
        )

    return plugins