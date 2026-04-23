def _handle_redirect(self, name_parts):
        module_utils_relative_parts = self._get_module_utils_remainder_parts(name_parts)

        # only allow redirects from below module_utils- if above that, bail out (eg, parent package names)
        if not module_utils_relative_parts:
            return False

        try:
            collection_metadata = _get_collection_metadata(self._collection_name)
        except ValueError as ve:  # collection not found or some other error related to collection load
            if self._is_optional:
                return False
            raise AnsibleError('error processing module_util {0} loading redirected collection {1}: {2}'
                               .format('.'.join(name_parts), self._collection_name, to_native(ve)))

        routing_entry = _nested_dict_get(collection_metadata, ['plugin_routing', 'module_utils', '.'.join(module_utils_relative_parts)])
        if not routing_entry:
            return False
        # FIXME: add deprecation warning support

        dep_or_ts = routing_entry.get('tombstone')
        removed = dep_or_ts is not None
        if not removed:
            dep_or_ts = routing_entry.get('deprecation')

        if dep_or_ts:
            removal_date = dep_or_ts.get('removal_date')
            removal_version = dep_or_ts.get('removal_version')
            warning_text = dep_or_ts.get('warning_text')

            msg = 'module_util {0} has been removed'.format('.'.join(name_parts))
            if warning_text:
                msg += ' ({0})'.format(warning_text)
            else:
                msg += '.'

            display.deprecated(  # pylint: disable=ansible-deprecated-date-not-permitted,ansible-deprecated-unnecessary-collection-name
                msg=msg,
                version=removal_version,
                removed=removed,
                date=removal_date,
                deprecator=deprecator_from_collection_name(self._collection_name),
            )
        if 'redirect' in routing_entry:
            self.redirected = True
            source_pkg = '.'.join(name_parts)
            self.is_package = True  # treat all redirects as packages
            redirect_target_pkg = routing_entry['redirect']

            # expand FQCN redirects
            if not redirect_target_pkg.startswith('ansible_collections'):
                split_fqcn = redirect_target_pkg.split('.')
                if len(split_fqcn) < 3:
                    raise Exception('invalid redirect for {0}: {1}'.format(source_pkg, redirect_target_pkg))
                # assume it's an FQCN, expand it
                redirect_target_pkg = 'ansible_collections.{0}.{1}.plugins.module_utils.{2}'.format(
                    split_fqcn[0],  # ns
                    split_fqcn[1],  # coll
                    '.'.join(split_fqcn[2:])  # sub-module_utils remainder
                )
            display.vvv('redirecting module_util {0} to {1}'.format(source_pkg, redirect_target_pkg))
            self.source_code = self._generate_redirect_shim_source(source_pkg, redirect_target_pkg)
            return True
        return False