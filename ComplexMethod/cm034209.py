def _get_plugin_list_descriptions(self, plugins: dict[str, _PluginDocMetadata]) -> dict[str, str]:

        descs = {}
        for plugin, plugin_info in plugins.items():
            # TODO: move to plugin itself i.e: plugin.get_desc()
            doc = None

            docerror = None
            if plugin_info.path:
                filename = Path(to_native(plugin_info.path))
                try:
                    doc = read_docstub(filename)
                except Exception as e:
                    docerror = e

            # plugin file was empty or had error, lets try other options
            if doc is None:
                # handle test/filters that are in file with diff name
                base = plugin.split('.')[-1]
                basefile = filename.with_name(base + filename.suffix)
                for extension in C.DOC_EXTENSIONS:
                    docfile = basefile.with_suffix(extension)
                    try:
                        if docfile.exists():
                            doc = read_docstub(docfile)
                    except Exception as e:
                        docerror = e

                # Do a final fallback to see if the plugin is a shadowed Jinja2 plugin
                # without any explicit documentation.
                if doc is None and plugin_info.jinja_builtin_short_description:
                    descs[plugin] = plugin_info.jinja_builtin_short_description
                    continue

                if docerror:
                    display.error_as_warning(f"{plugin} has a documentation formatting error.", exception=docerror)
                    continue

            if not doc or not isinstance(doc, dict):
                desc = 'UNDOCUMENTED'
            else:
                desc = doc.get('short_description', 'INVALID SHORT DESCRIPTION').strip()

            descs[plugin] = desc

        return descs