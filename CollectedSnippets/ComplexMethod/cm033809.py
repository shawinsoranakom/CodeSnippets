def _check_for_new_args(self, doc):
        if not self.base_module:
            return

        with CaptureStd():
            try:
                existing_doc, dummy_examples, dummy_return, existing_metadata = get_docstring(
                    os.path.abspath(self.base_module), fragment_loader, verbose=True, collection_name=self.collection_name,
                    is_module=self.plugin_type == 'module')
                existing_options = existing_doc.get('options', {}) or {}
            except AssertionError:
                fragment = doc['extends_documentation_fragment']
                self.reporter.warning(
                    path=self.object_path,
                    code='missing-existing-doc-fragment',
                    msg='Pre-existing DOCUMENTATION fragment missing: %s' % fragment
                )
                return
            except Exception as e:
                self.reporter.warning_trace(
                    path=self.object_path,
                    tracebk=e
                )
                self.reporter.warning(
                    path=self.object_path,
                    code='unknown-doc-fragment',
                    msg=('Unknown pre-existing DOCUMENTATION error, see TRACE. Submodule refs may need updated')
                )
                return

        try:
            mod_collection_name = existing_doc.get('version_added_collection')
            mod_version_added = self._create_strict_version(
                str(existing_doc.get('version_added', '0.0')),
                collection_name=mod_collection_name)
        except ValueError:
            mod_collection_name = self.collection_name
            mod_version_added = self._create_strict_version('0.0')

        options = doc.get('options', {}) or {}

        should_be = '.'.join(ansible_version.split('.')[:2])
        strict_ansible_version = self._create_strict_version(should_be, collection_name='ansible.builtin')

        for option, details in options.items():
            try:
                names = [option] + details.get('aliases', [])
            except (TypeError, AttributeError):
                # Reporting of this syntax error will be handled by schema validation.
                continue

            if any(name in existing_options for name in names):
                # The option already existed. Make sure version_added didn't change.
                for name in names:
                    existing_collection_name = existing_options.get(name, {}).get('version_added_collection')
                    existing_version = existing_options.get(name, {}).get('version_added')
                    if existing_version:
                        break
                current_collection_name = details.get('version_added_collection')
                current_version = details.get('version_added')
                if current_collection_name != existing_collection_name:
                    self.reporter.error(
                        path=self.object_path,
                        code='option-incorrect-version-added-collection',
                        msg=('version_added for existing option (%s) should '
                             'belong to collection %r. Currently belongs to %r' %
                             (option, current_collection_name, existing_collection_name))
                    )
                elif str(current_version) != str(existing_version):
                    self.reporter.error(
                        path=self.object_path,
                        code='option-incorrect-version-added',
                        msg=('version_added for existing option (%s) should '
                             'be %r. Currently %r' %
                             (option, existing_version, current_version))
                    )
                continue

            try:
                collection_name = details.get('version_added_collection')
                version_added = self._create_strict_version(
                    str(details.get('version_added', '0.0')),
                    collection_name=collection_name)
            except ValueError as e:
                # already reported during schema validation
                continue

            builtin = self.collection_name == 'ansible.builtin' and collection_name in ('ansible.builtin', None)
            if not builtin and collection_name != self.collection_name:
                continue
            if (strict_ansible_version != mod_version_added and
                    (version_added < strict_ansible_version or
                     strict_ansible_version < version_added)):
                self.reporter.error(
                    path=self.object_path,
                    code='option-incorrect-version-added',
                    msg=('version_added for new option (%s) should '
                         'be %r. Currently %r' %
                         (option, should_be, version_added))
                )

        return existing_doc