def _validate_ansible_module_call(self, docs):
        try:
            if self._python_module():
                spec, kwargs = get_py_argument_spec(self.path, self.collection)
            elif self._powershell_module():
                spec, kwargs = get_ps_argument_spec(self.path, self.collection)
            else:
                raise NotImplementedError()
        except AnsibleModuleNotInitialized:
            self.reporter.error(
                path=self.object_path,
                code='ansible-module-not-initialized',
                msg="Execution of the module did not result in initialization of AnsibleModule",
            )
            return
        except AnsibleModuleImportError as e:
            self.reporter.error(
                path=self.object_path,
                code='import-error',
                msg="Exception attempting to import module for argument_spec introspection, '%s'" % e
            )
            self.reporter.trace(
                path=self.object_path,
                tracebk=traceback.format_exc()
            )
            return

        schema = ansible_module_kwargs_schema(self.object_name.split('.')[0], for_collection=bool(self.collection))
        self._validate_docs_schema(kwargs, schema, 'AnsibleModule', 'invalid-ansiblemodule-schema')

        self._validate_argument_spec(docs, spec, kwargs)

        if isinstance(docs, Mapping) and isinstance(docs.get('attributes'), Mapping):
            if isinstance(docs['attributes'].get('check_mode'), Mapping):
                support_value = docs['attributes']['check_mode'].get('support')
                if not kwargs.get('supports_check_mode', False):
                    if support_value != 'none':
                        self.reporter.error(
                            path=self.object_path,
                            code='attributes-check-mode',
                            msg="The module does not declare support for check mode, but the check_mode attribute's"
                                " support value is '%s' and not 'none'" % support_value
                        )
                else:
                    if support_value not in ('full', 'partial', 'N/A'):
                        self.reporter.error(
                            path=self.object_path,
                            code='attributes-check-mode',
                            msg="The module does declare support for check mode, but the check_mode attribute's support value is '%s'" % support_value
                        )
                if support_value in ('partial', 'N/A') and docs['attributes']['check_mode'].get('details') in (None, '', []):
                    self.reporter.error(
                        path=self.object_path,
                        code='attributes-check-mode-details',
                        msg="The module declares it does not fully support check mode, but has no details on what exactly that means"
                    )