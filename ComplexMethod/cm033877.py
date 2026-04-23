def _resolve_plugin_step(
        self,
        name: str,
        mod_type: str = '',
        check_aliases: bool = False,
        collection_list: list[str] | None = None,
        plugin_load_context: PluginLoadContext | None = None,
    ) -> PluginLoadContext:
        if not plugin_load_context:
            raise ValueError('A PluginLoadContext is required')

        plugin_load_context.redirect_list.append(name)
        plugin_load_context.resolved = False

        if name in _PLUGIN_FILTERS[self.package]:
            plugin_load_context.exit_reason = '{0} matched a defined plugin filter'.format(name)
            return plugin_load_context

        if mod_type:
            suffix = mod_type
        elif self.class_name:
            # Ansible plugins that run in the controller process (most plugins)
            suffix = '.py'
        else:
            # Only Ansible Modules.  Ansible modules can be any executable so
            # they can have any suffix
            suffix = ''

        # FIXME: need this right now so we can still load shipped PS module_utils- come up with a more robust solution
        if (AnsibleCollectionRef.is_valid_fqcr(name) or collection_list) and not name.startswith('Ansible'):
            if '.' in name or not collection_list:
                candidates = [name]
            else:
                candidates = ['{0}.{1}'.format(c, name) for c in collection_list]

            for candidate_name in candidates:
                try:
                    plugin_load_context.load_attempts.append(candidate_name)
                    # HACK: refactor this properly
                    if candidate_name.startswith('ansible.legacy'):
                        # 'ansible.legacy' refers to the plugin finding behavior used before collections existed.
                        # They need to search 'library' and the various '*_plugins' directories in order to find the file.
                        plugin_load_context = self._find_plugin_legacy(name.removeprefix('ansible.legacy.'),
                                                                       plugin_load_context, check_aliases, suffix)
                    else:
                        # 'ansible.builtin' should be handled here. This means only internal, or builtin, paths are searched.
                        plugin_load_context = self._find_fq_plugin(candidate_name, suffix, plugin_load_context=plugin_load_context)

                        # Pending redirects are added to the redirect_list at the beginning of _resolve_plugin_step.
                        # Once redirects are resolved, ensure the final FQCN is added here.
                        # e.g. 'ns.coll.module' is included rather than only 'module' if a collections list is provided:
                        # - module:
                        #   collections: ['ns.coll']
                        if plugin_load_context.resolved and candidate_name not in plugin_load_context.redirect_list:
                            plugin_load_context.redirect_list.append(candidate_name)

                    if plugin_load_context.resolved or plugin_load_context.pending_redirect:  # if we got an answer or need to chase down a redirect, return
                        return plugin_load_context
                except (AnsiblePluginRemovedError, AnsiblePluginCircularRedirect, AnsibleCollectionUnsupportedVersionError):
                    # these are generally fatal, let them fly
                    raise
                except Exception as ex:
                    plugin_load_context.raw_error_list.append(ex)

                    # DTFIX-FUTURE: can we deprecate/remove these stringified versions?
                    if isinstance(ex, ImportError):
                        plugin_load_context.import_error_list.append(ex)
                    else:
                        plugin_load_context.error_list.append(str(ex))

            if plugin_load_context.error_list:
                display.debug(msg='plugin lookup for {0} failed; errors: {1}'.format(name, '; '.join(plugin_load_context.error_list)))

            plugin_load_context.exit_reason = 'no matches found for {0}'.format(name)

            return plugin_load_context

        # if we got here, there's no collection list and it's not an FQ name, so do legacy lookup

        return self._find_plugin_legacy(name, plugin_load_context, check_aliases, suffix)