def parse_source(self, source, cache=False):
        """ Generate or update inventory for the source provided """

        parsed = False
        failures = []
        display.debug(u'Examining possible inventory source: %s' % source)

        # use binary for path functions
        b_source = to_bytes(source)

        # process directories as a collection of inventories
        if os.path.isdir(b_source):
            display.debug(u'Searching for inventory files in directory: %s' % source)
            for i in sorted(os.listdir(b_source)):

                display.debug(u'Considering %s' % i)
                # Skip hidden files and stuff we explicitly ignore
                if IGNORED.search(i):
                    continue

                # recursively deal with directory entries
                fullpath = to_text(os.path.join(b_source, i), errors='surrogate_or_strict')
                parsed_this_one = self.parse_source(fullpath, cache=cache)
                display.debug(u'parsed %s as %s' % (fullpath, parsed_this_one))
                if not parsed:
                    parsed = parsed_this_one
        else:
            # left with strings or files, let plugins figure it out

            # set so new hosts can use for inventory_file/dir vars
            self._inventory.current_source = source

            # try source with each plugin
            for plugin in self._fetch_inventory_plugins():
                plugin_name = to_text(getattr(plugin, '_load_name', getattr(plugin, '_original_path', '')))
                display.debug(u'Attempting to use plugin %s (%s)' % (plugin_name, plugin._original_path))

                # initialize and figure out if plugin wants to attempt parsing this file
                try:
                    plugin_wants = bool(plugin.verify_file(source))
                except Exception:
                    plugin_wants = False

                if plugin_wants:
                    # have this tag ready to apply to errors or output; str-ify source since it is often tagged by the CLI
                    origin = Origin(description=f'<inventory plugin {plugin_name!r} with source {str(source)!r}>')
                    try:
                        inventory_wrapper = _InventoryDataWrapper(self._inventory, target_plugin=plugin, origin=origin)

                        # FUTURE: now that we have a wrapper around inventory, we can have it use ChainMaps to preview the in-progress inventory,
                        #  but be able to roll back partial inventory failures by discarding the outermost layer
                        plugin.parse(inventory_wrapper, self._loader, source, cache=cache)
                        try:
                            plugin.update_cache_if_changed()
                        except AttributeError:
                            # some plugins might not implement caching
                            pass
                        parsed = True
                        display.vvv('Parsed %s inventory source with %s plugin' % (source, plugin_name))
                        break
                    except AnsibleError as ex:
                        if not ex.obj:
                            ex.obj = origin
                        failures.append({'src': source, 'plugin': plugin_name, 'exc': ex})
                    except Exception as ex:
                        # DTFIX-FUTURE: fix this error handling to correctly deal with messaging
                        try:
                            # omit line number to prevent contextual display of script or possibly sensitive info
                            raise AnsibleError(str(ex), obj=origin) from ex
                        except AnsibleError as ex:
                            failures.append({'src': source, 'plugin': plugin_name, 'exc': ex})
                else:
                    display.vvv("%s declined parsing %s as it did not pass its verify_file() method" % (plugin_name, source))

        if parsed:
            self._inventory.processed_sources.append(self._inventory.current_source)
        else:
            # only warn/error if NOT using the default or using it and the file is present
            # TODO: handle 'non file' inventory and detect vs hardcode default
            if source != '/etc/ansible/hosts' or os.path.exists(source):

                if failures:
                    # only if no plugin processed files should we show errors.
                    for fail in failures:
                        # `obj` should always be set
                        display.error_as_warning(msg=f'Failed to parse inventory with {fail["plugin"]!r} plugin.', exception=fail['exc'])

                # final error/warning on inventory source failure
                if C.INVENTORY_ANY_UNPARSED_IS_FAILED:
                    raise AnsibleError(u'Completely failed to parse inventory source %s' % (source))
                else:
                    display.warning("Unable to parse %s as an inventory source" % source)

        # clear up, jic
        self._inventory.current_source = None

        return parsed