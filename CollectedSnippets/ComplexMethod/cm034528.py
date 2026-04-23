def find_plugin_docfile(plugin, plugin_type, loader):
    """  if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding 'sidecar' file for docs """

    context = loader.find_plugin_with_context(plugin, ignore_deprecated=False, check_aliases=True)
    if (not context or not context.resolved) and plugin_type in ('filter', 'test'):
        # should only happen for filters/test
        plugin_obj, context = loader.get_with_context(plugin)

    if not context or not context.resolved:
        raise AnsiblePluginNotFound('%s was not found' % (plugin), plugin_load_context=context)

    docfile = Path(context.plugin_resolved_path)
    if docfile.suffix not in C.DOC_EXTENSIONS:
        # only look for adjacent if plugin file does not support documents
        filenames = _find_adjacent(docfile, plugin, C.DOC_EXTENSIONS)
        filename = filenames[0] if filenames else None
    else:
        filename = to_native(docfile)

    if filename is None:
        raise AnsibleError('%s cannot contain DOCUMENTATION nor does it have a companion documentation file' % (plugin))

    return filename, context