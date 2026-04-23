def validate(self):
        super(ModuleValidator, self).validate()
        if not self._python_module() and not self._powershell_module() and not self._sidecar_doc():
            self.reporter.error(
                path=self.object_path,
                code='invalid-extension',
                msg=('Official Ansible modules must have a .py '
                     'extension for python modules or a .ps1 '
                     'for powershell modules')
            )

        if self._python_module() and self.ast is None:
            self.reporter.error(
                path=self.object_path,
                code='python-syntax-error',
                msg='Python SyntaxError while parsing module'
            )
            try:
                compile(self.text, self.path, 'exec')
            except Exception:
                self.reporter.trace(
                    path=self.object_path,
                    tracebk=traceback.format_exc()
                )
            return

        end_of_deprecation_should_be_removed_only = False
        doc_info = None
        if self._python_module() or self._sidecar_doc():
            doc_info, docs = self._validate_docs()

            # See if current version => deprecated.removed_in, ie, should be docs only
            if docs and docs.get('deprecated', False):

                if 'removed_in' in docs['deprecated']:
                    removed_in = None
                    collection_name = docs['deprecated'].get('removed_from_collection')
                    version = docs['deprecated']['removed_in']
                    if collection_name != self.collection_name:
                        self.reporter.error(
                            path=self.object_path,
                            code='invalid-module-deprecation-source',
                            msg=('The deprecation version for a module must be added in this collection')
                        )
                    else:
                        try:
                            removed_in = self._create_strict_version(str(version), collection_name=collection_name)
                        except ValueError as e:
                            self.reporter.error(
                                path=self.object_path,
                                code='invalid-module-deprecation-version',
                                msg=('The deprecation version %r cannot be parsed: %s' % (version, e))
                            )

                    if removed_in:
                        if not self.collection:
                            strict_ansible_version = self._create_strict_version(
                                '.'.join(ansible_version.split('.')[:2]), self.collection_name)
                            end_of_deprecation_should_be_removed_only = strict_ansible_version >= removed_in

                            if end_of_deprecation_should_be_removed_only:
                                self.reporter.error(
                                    path=self.object_path,
                                    code='ansible-deprecated-module',
                                    msg='Module is marked for removal in version %s of Ansible when the current version is %s' % (
                                        version, ansible_version),
                                )
                        elif self.collection_version:
                            strict_ansible_version = self.collection_version
                            end_of_deprecation_should_be_removed_only = strict_ansible_version >= removed_in

                            if end_of_deprecation_should_be_removed_only:
                                self.reporter.error(
                                    path=self.object_path,
                                    code='collection-deprecated-module',
                                    msg='Module is marked for removal in version %s of this collection when the current version is %s' % (
                                        version, self.collection_version_str),
                                )

                # handle deprecation by date
                if 'removed_at_date' in docs['deprecated']:
                    try:
                        removed_at_date = docs['deprecated']['removed_at_date']
                        if parse_isodate(removed_at_date, allow_date=True) < datetime.date.today():
                            msg = "Module's deprecated.removed_at_date date '%s' is before today" % removed_at_date
                            self.reporter.error(path=self.object_path, code='deprecated-date', msg=msg)
                    except ValueError:
                        # This happens if the date cannot be parsed. This is already checked by the schema.
                        pass

        if self._python_module() and not self._just_docs() and not end_of_deprecation_should_be_removed_only:
            if self.plugin_type == 'module':
                self._validate_ansible_module_call(docs)
            self._check_for_sys_exit()
            self._find_rejectlist_imports()
            if self.plugin_type == 'module':
                self._find_module_utils()
            self._find_has_import()

            if doc_info:
                first_callable = self._get_first_callable() or 1000000  # use a bogus "high" line number if no callable exists
                self._ensure_imports_below_docs(doc_info, first_callable)

        if self._powershell_module():
            self._validate_ps_replacers()
            docs_path = self._find_ps_docs_file()

            # We can only validate PowerShell arg spec if it is using the new Ansible.Basic.AnsibleModule util
            pattern = r'(?im)^#\s*ansiblerequires\s+\-csharputil\s*Ansible\.Basic'
            if re.search(pattern, self.text) and self.object_name not in self.PS_ARG_VALIDATE_REJECTLIST:
                with ModuleValidator(docs_path, git_cache=self.git_cache) as docs_mv:
                    docs = docs_mv._validate_docs()[1]
                    self._validate_ansible_module_call(docs)

        self._check_gpl3_header()
        if not self._just_docs() and not self._sidecar_doc() and not end_of_deprecation_should_be_removed_only:
            if self.plugin_type == 'module':
                self._check_interpreter()