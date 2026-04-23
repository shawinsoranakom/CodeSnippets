def _validate_docs(self):
        doc = None
        # We have two ways of marking deprecated/removed files. Have to check each one
        # individually and then make sure they all agree
        doc_deprecated = None  # doc legally might not exist
        routing_says_deprecated = False

        if self.routing:
            routing_deprecation = self.routing.get('plugin_routing', {})
            routing_deprecation = routing_deprecation.get('modules' if self.plugin_type == 'module' else self.plugin_type, {})
            routing_deprecation = routing_deprecation.get(self.name, {}).get('deprecation', {})
            if routing_deprecation:
                # consult meta/runtime.yml for collection to see if this is deprecated
                # consult ansible_builtin_runtime.yml for ansible.builtin to see if this is deprecated
                routing_says_deprecated = True

        if self._python_module():
            doc_info = self._get_py_docs()
        else:
            doc_info = None

        sidecar_text = None
        if self._sidecar_doc():
            sidecar_text = self.text
        elif sidecar_path := self._find_sidecar_docs():
            with open(sidecar_path, mode='r', encoding='utf-8') as fd:
                sidecar_text = fd.read()

        if sidecar_text:
            sidecar_doc, errors, traces = parse_yaml(sidecar_text, 0, self.name, 'DOCUMENTATION')
            for error in errors:
                self.reporter.error(
                    path=self.object_path,
                    code='documentation-syntax-error',
                    **error
                )
            for trace in traces:
                self.reporter.trace(
                    path=self.object_path,
                    tracebk=trace
                )

            doc = sidecar_doc.get('DOCUMENTATION', None)
            examples_raw = sidecar_doc.get('EXAMPLES', None)
            examples_lineno = 1
            returns = sidecar_doc.get('RETURN', None)

        elif doc_info:
            if bool(doc_info['DOCUMENTATION']['value']):
                doc, errors, traces = parse_yaml(
                    doc_info['DOCUMENTATION']['value'],
                    doc_info['DOCUMENTATION']['lineno'],
                    self.name, 'DOCUMENTATION'
                )

                for error in errors:
                    self.reporter.error(
                        path=self.object_path,
                        code='documentation-syntax-error',
                        **error
                    )
                for trace in traces:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=trace
                    )

            examples_raw = doc_info['EXAMPLES']['value']
            examples_lineno = doc_info['EXAMPLES']['lineno']

            returns = None
            if bool(doc_info['RETURN']['value']):
                returns, errors, traces = parse_yaml(doc_info['RETURN']['value'],
                                                     doc_info['RETURN']['lineno'],
                                                     self.name, 'RETURN')

                for error in errors:
                    self.reporter.error(
                        path=self.object_path,
                        code='return-syntax-error',
                        **error
                    )
                for trace in traces:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=trace
                    )

        if doc:
            add_collection_to_versions_and_dates(doc, self.collection_name,
                                                 is_module=self.plugin_type == 'module')

            with CaptureStd():
                try:
                    get_docstring(os.path.abspath(self.path), fragment_loader=fragment_loader,
                                  verbose=True,
                                  collection_name=self.collection_name,
                                  plugin_type=self.plugin_type)
                except AnsibleFragmentError:
                    # Will be re-triggered below when explicitly calling add_fragments()
                    pass
                except Exception as e:
                    self.reporter.trace(
                        path=self.object_path,
                        tracebk=traceback.format_exc()
                    )
                    self.reporter.error(
                        path=self.object_path,
                        code='documentation-error',
                        msg='Unknown DOCUMENTATION error, see TRACE: %s' % e
                    )

            try:
                add_fragments(doc, os.path.abspath(self.object_path), fragment_loader=fragment_loader,
                              is_module=self.plugin_type == 'module', section='DOCUMENTATION')
            except AnsibleFragmentError as exc:
                error = str(exc).replace(os.path.abspath(self.object_path), self.object_path)
                self.reporter.error(
                    path=self.object_path,
                    code='doc-fragment-error',
                    msg=f'Error while adding fragments: {error}'
                )

            if 'options' in doc and doc['options'] is None:
                self.reporter.error(
                    path=self.object_path,
                    code='invalid-documentation-options',
                    msg='DOCUMENTATION.options must be a dictionary/hash when used',
                )

            if 'deprecated' in doc and doc.get('deprecated'):
                doc_deprecated = True
                doc_deprecation = doc['deprecated']
                documentation_collection = doc_deprecation.get('removed_from_collection')
                if documentation_collection != self.collection_name:
                    self.reporter.error(
                        path=self.object_path,
                        code='deprecation-wrong-collection',
                        msg='"DOCUMENTATION.deprecation.removed_from_collection must be the current collection name: %r vs. %r' % (
                            documentation_collection, self.collection_name)
                    )
            else:
                doc_deprecated = False

            if os.path.islink(self.object_path):
                # This module has an alias, which we can tell as it's a symlink
                # Rather than checking for `module: $filename` we need to check against the true filename
                module_name = os.readlink(self.object_path).split('.')[0]
            else:
                # This is the normal case
                module_name = self.object_name.split('.')[0]

            self._validate_docs_schema(
                doc,
                doc_schema(
                    module_name,
                    for_collection=bool(self.collection),
                    deprecated_module=routing_says_deprecated or doc_deprecated,
                    plugin_type=self.plugin_type,
                ),
                'DOCUMENTATION',
                'invalid-documentation',
            )

            if doc:
                self._validate_option_docs(doc.get('options'))

            self._validate_all_semantic_markup(doc, returns)

            if not self.collection:
                existing_doc = self._check_for_new_args(doc)
                self._check_version_added(doc, existing_doc)
        else:
            self.reporter.error(
                path=self.object_path,
                code='missing-documentation',
                msg='No DOCUMENTATION provided',
            )

        if not examples_raw and self.plugin_type in PLUGINS_WITH_EXAMPLES:
            if self.plugin_type in PLUGINS_WITH_EXAMPLES:
                self.reporter.error(
                    path=self.object_path,
                    code='missing-examples',
                    msg='No EXAMPLES provided'
                )

        elif self.plugin_type in PLUGINS_WITH_YAML_EXAMPLES:
            dummy, errors, traces = parse_yaml(examples_raw,
                                               examples_lineno,
                                               self.name, 'EXAMPLES',
                                               load_all=True,
                                               ansible_loader=True)
            for error in errors:
                self.reporter.error(
                    path=self.object_path,
                    code='invalid-examples',
                    **error
                )
            for trace in traces:
                self.reporter.trace(
                    path=self.object_path,
                    tracebk=trace
                )

        if returns:
            if returns:
                add_collection_to_versions_and_dates(
                    returns,
                    self.collection_name,
                    is_module=self.plugin_type == 'module',
                    return_docs=True)
                try:
                    add_fragments(returns, os.path.abspath(self.object_path), fragment_loader=fragment_loader,
                                  is_module=self.plugin_type == 'module', section='RETURN')
                except AnsibleFragmentError as exc:
                    error = str(exc).replace(os.path.abspath(self.object_path), self.object_path)
                    self.reporter.error(
                        path=self.object_path,
                        code='return-fragment-error',
                        msg=f'Error while adding fragments: {error}'
                    )
            self._validate_docs_schema(
                returns,
                return_schema(for_collection=bool(self.collection), plugin_type=self.plugin_type),
                'RETURN', 'return-syntax-error')
            self._validate_return_docs(returns)

        elif self.plugin_type in PLUGINS_WITH_RETURN_VALUES:
            if self._is_new_module():
                self.reporter.error(
                    path=self.object_path,
                    code='missing-return',
                    msg='No RETURN provided'
                )
            else:
                self.reporter.warning(
                    path=self.object_path,
                    code='missing-return-legacy',
                    msg='No RETURN provided'
                )

        # Check for mismatched deprecation
        if not self.collection:
            if doc_deprecated != routing_says_deprecated:
                self.reporter.error(
                    path=self.object_path,
                    code='deprecation-mismatch',
                    msg='Module deprecation/removed must agree in documentation, by adding an entry in ansible_builtin_runtime.yml'
                        ' and setting DOCUMENTATION.deprecated for deprecation or by removing all'
                        ' documentation for removed'
                )
        else:
            if not (doc_deprecated == routing_says_deprecated):
                # DOCUMENTATION.deprecated and meta/runtime.yml disagree
                self.reporter.error(
                    path=self.object_path,
                    code='deprecation-mismatch',
                    msg='"meta/runtime.yml" and DOCUMENTATION.deprecation do not agree.'
                )
            elif routing_says_deprecated:
                # Both DOCUMENTATION.deprecated and meta/runtime.yml agree that the module is deprecated.
                # Make sure they give the same version or date.
                routing_date = routing_deprecation.get('removal_date')
                routing_version = routing_deprecation.get('removal_version')
                # The versions and dates in the module documentation are auto-tagged, so remove the tag
                # to make comparison possible and to avoid confusing the user.
                documentation_date = doc_deprecation.get('removed_at_date')
                documentation_version = doc_deprecation.get('removed_in')
                if not compare_dates(routing_date, documentation_date):
                    self.reporter.error(
                        path=self.object_path,
                        code='deprecation-mismatch',
                        msg='"meta/runtime.yml" and DOCUMENTATION.deprecation do not agree on removal date: %r vs. %r' % (
                            routing_date, documentation_date)
                    )
                if routing_version != documentation_version:
                    self.reporter.error(
                        path=self.object_path,
                        code='deprecation-mismatch',
                        msg='"meta/runtime.yml" and DOCUMENTATION.deprecation do not agree on removal version: %r vs. %r' % (
                            routing_version, documentation_version)
                    )

            # In the future we should error if ANSIBLE_METADATA exists in a collection

        return doc_info, doc