def _find_fq_plugin(
        self,
        fq_name: str,
        extension: str | None,
        plugin_load_context: PluginLoadContext,
    ) -> PluginLoadContext:
        """Search builtin paths to find a plugin. No external paths are searched,
        meaning plugins inside roles inside collections will be ignored.
        """

        plugin_load_context.resolved = False

        plugin_type = AnsibleCollectionRef.legacy_plugin_dir_to_plugin_type(self.subdir)

        acr = AnsibleCollectionRef.from_fqcr(fq_name, plugin_type)

        # check collection metadata to see if any special handling is required for this plugin
        routing_metadata = self._query_collection_routing_meta(acr, plugin_type, extension=extension)

        action_plugin = None
        # TODO: factor this into a wrapper method
        if routing_metadata:
            deprecation = routing_metadata.get('deprecation', None)

            # this will no-op if there's no deprecation metadata for this plugin
            plugin_load_context.record_deprecation(fq_name, deprecation, acr.collection)

            tombstone = routing_metadata.get('tombstone', None)

            # FIXME: clean up text gen
            if tombstone:
                removal_date = tombstone.get('removal_date')
                removal_version = tombstone.get('removal_version')
                warning_text = tombstone.get('warning_text') or ''
                warning_plugin_type = "module" if self.type == "modules" else f'{self.type} plugin'
                warning_text = f'The {fq_name!r} {warning_plugin_type} has been removed.{" " if warning_text else ""}{warning_text}'
                removed_msg = _display_utils.get_deprecation_message_with_plugin_info(
                    msg=warning_text,
                    version=removal_version,
                    date=removal_date,
                    removed=True,
                    deprecator=deprecator_from_collection_name(acr.collection),
                )
                plugin_load_context.date = removal_date
                plugin_load_context.version = removal_version
                plugin_load_context.resolved = True
                plugin_load_context.exit_reason = removed_msg
                raise AnsiblePluginRemovedError(message=removed_msg, plugin_load_context=plugin_load_context)

            redirect = routing_metadata.get('redirect', None)

            if redirect:
                # Prevent mystery redirects that would be determined by the collections keyword
                if not AnsibleCollectionRef.is_valid_fqcr(redirect):
                    raise AnsibleError(
                        f"Collection {acr.collection} contains invalid redirect for {fq_name}: {redirect}. "
                        "Redirects must use fully qualified collection names."
                    )

                # FIXME: remove once this is covered in debug or whatever
                display.vv("redirecting (type: {0}) {1} to {2}".format(plugin_type, fq_name, redirect))

                # The name doing the redirection is added at the beginning of _resolve_plugin_step,
                # but if the unqualified name is used in conjunction with the collections keyword, only
                # the unqualified name is in the redirect list.
                if fq_name not in plugin_load_context.redirect_list:
                    plugin_load_context.redirect_list.append(fq_name)
                return plugin_load_context.redirect(redirect)
                # TODO: non-FQCN case, do we support `.` prefix for current collection, assume it with no dots, require it for subdirs in current, or ?

            if self.type == 'modules':
                action_plugin = routing_metadata.get('action_plugin')

        n_resource = to_native(acr.resource, errors='strict')
        # we want this before the extension is added
        full_name = '{0}.{1}'.format(acr.n_python_package_name, n_resource)

        if extension:
            n_resource += extension

        pkg = sys.modules.get(acr.n_python_package_name)
        if not pkg:
            # FIXME: there must be cheaper/safer way to do this
            try:
                pkg = import_module(acr.n_python_package_name)
            except ImportError:
                return plugin_load_context.nope('Python package {0} not found'.format(acr.n_python_package_name))

        pkg_path = os.path.dirname(pkg.__file__)

        n_resource_path = os.path.join(pkg_path, n_resource)

        # FIXME: and is file or file link or ...
        if os.path.exists(n_resource_path):
            return plugin_load_context.resolve(
                full_name, to_text(n_resource_path), acr.collection, 'found exact match for {0} in {1}'.format(full_name, acr.collection), action_plugin)

        if extension:
            # the request was extension-specific, don't try for an extensionless match
            return plugin_load_context.nope('no match for {0} in {1}'.format(to_text(n_resource), acr.collection))

        # look for any matching extension in the package location (sans filter)
        found_files = [f
                       for f in glob.iglob(os.path.join(pkg_path, n_resource) + '.*')
                       if os.path.isfile(f) and not any(f.endswith(ext) for ext in C.MODULE_IGNORE_EXTS)]

        if not found_files:
            return plugin_load_context.nope('failed fuzzy extension match for {0} in {1}'.format(full_name, acr.collection))

        found_files = sorted(found_files)  # sort to ensure deterministic results, with the shortest match first

        if len(found_files) > 1:
            display.debug('Found several possible candidates for the plugin but using first: %s' % ','.join(found_files))

        return plugin_load_context.resolve(
            full_name, to_text(found_files[0]), acr.collection,
            'found fuzzy extension match for {0} in {1}'.format(full_name, acr.collection), action_plugin)