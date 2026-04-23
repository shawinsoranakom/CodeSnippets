def _list_plugins_from_paths(ptype, dirs, collection, depth=0, docs=False):
    # TODO: update to use importlib.resources

    plugins = {}

    for path in dirs:
        display.debug("Searching '{0}'s '{1}' for {2} plugins".format(collection, path, ptype))
        b_path = to_bytes(path)

        if os.path.basename(b_path).startswith((b'.', b'__')):
            # skip hidden/special dirs
            continue

        if os.path.exists(b_path):
            if os.path.isdir(b_path):
                bkey = ptype.lower()
                for plugin_file in os.listdir(b_path):

                    if plugin_file.startswith((b'.', b'__')):
                        # hidden or python internal file/dir
                        continue

                    display.debug("Found possible plugin: '{0}'".format(plugin_file))
                    b_plugin, b_ext = os.path.splitext(plugin_file)
                    plugin = to_native(b_plugin)
                    full_path = os.path.join(b_path, plugin_file)

                    if os.path.isdir(full_path):
                        # its a dir, recurse
                        if collection in C.SYNTHETIC_COLLECTIONS:
                            if not os.path.exists(os.path.join(full_path, b'__init__.py')):
                                # dont recurse for synthetic unless init.py present
                                continue

                        # actually recurse dirs
                        plugins.update(_list_plugins_from_paths(ptype, [to_native(full_path)], collection, depth=depth + 1, docs=docs))
                    else:
                        if any([
                                plugin in C.IGNORE_FILES,                # general files to ignore
                                to_native(b_ext) in C.REJECT_EXTS,       # general extensions to ignore
                                b_ext in (b'.yml', b'.yaml', b'.json'),  # ignore docs files
                                plugin in IGNORE.get(bkey, ()),          # plugin in reject list
                                os.path.islink(full_path),               # skip aliases, author should document in 'aliases' field
                                not docs and b_ext in (b''),             # ignore no ext when looking for docs files
                        ]):
                            continue

                        resource_dir = to_native(os.path.dirname(full_path))
                        resource_name = get_composite_name(collection, plugin, resource_dir, depth)

                        if ptype in ('test', 'filter'):
                            # NOTE: pass the composite resource to ensure any relative
                            # imports it contains are interpreted in the correct context
                            if collection:
                                resource_name = '.'.join(resource_name.split('.')[2:])
                            try:
                                file_plugins = _list_j2_plugins_from_file(collection, full_path, ptype, resource_name)
                            except KeyError as e:
                                display.warning('Skipping file %s: %s' % (full_path, to_native(e)))
                                continue

                            for plugin in file_plugins:
                                plugin_name = get_composite_name(collection, plugin.ansible_name, resource_dir, depth)
                                plugins[plugin_name] = full_path
                        else:
                            plugin_name = resource_name
                            plugins[plugin_name] = full_path
            else:
                display.debug("Skip listing plugins in '{0}' as it is not a directory".format(path))
        else:
            display.debug("Skip listing plugins in '{0}' as it does not exist".format(path))

    return plugins