def _validate_ps_replacers(self):
        # loop all (for/else + error)
        # get module list for each
        # check "shape" of each module name

        legacy_ps_requires = r'(?im)^#\s*Requires\s+\-Module(?:s?)\s+(Ansible\.ModuleUtils\..+)'
        ps_requires = r"""(?imx)
            ^\#\s*AnsibleRequires\s+-PowerShell\s+
            (
                # Builtin PowerShell module
                (Ansible\.ModuleUtils\.[\w\.]+)
                |
                # Fully qualified collection PowerShell module
                (ansible_collections\.\w+\.\w+\.plugins\.module_utils\.[\w\.]+)
                |
                # Relative collection PowerShell module
                (\.[\w\.]+)
            )
            (\s+-Optional)?"""
        csharp_requires = r"""(?imx)
            ^\#\s*AnsibleRequires\s+-CSharpUtil\s+
            (
                # Builtin C# util
                (Ansible\.[\w\.]+)
                |
                # Fully qualified collection C# util
                (ansible_collections\.\w+\.\w+\.plugins\.module_utils\.[\w\.]+)
                |
                # Relative collection C# util
                (\.[\w\.]+)
            )
            (\s+-Optional)?"""

        found_requires = False

        for pattern, required_type in [(legacy_ps_requires, "Requires"), (ps_requires, "AnsibleRequires")]:
            for req_stmt in re.finditer(pattern, self.text):
                found_requires = True
                # this will bomb on dictionary format - "don't do that"
                module_list = [x.strip() for x in req_stmt.group(1).split(',')]
                if len(module_list) > 1:
                    self.reporter.error(
                        path=self.object_path,
                        code='multiple-utils-per-requires',
                        msg='Ansible.ModuleUtils requirements do not support multiple modules per statement: "%s"' % req_stmt.group(0)
                    )
                    continue

                module_name = module_list[0]

                if module_name.lower().endswith('.psm1'):
                    self.reporter.error(
                        path=self.object_path,
                        code='invalid-requires-extension',
                        msg='Module #%s should not end in .psm1: "%s"' % (required_type, module_name)
                    )

        for req_stmt in re.finditer(csharp_requires, self.text):
            found_requires = True
            # this will bomb on dictionary format - "don't do that"
            module_list = [x.strip() for x in req_stmt.group(1).split(',')]
            if len(module_list) > 1:
                self.reporter.error(
                    path=self.object_path,
                    code='multiple-csharp-utils-per-requires',
                    msg='Ansible C# util requirements do not support multiple utils per statement: "%s"' % req_stmt.group(0)
                )
                continue

            module_name = module_list[0]

            if module_name.lower().endswith('.cs'):
                self.reporter.error(
                    path=self.object_path,
                    code='illegal-extension-cs',
                    msg='Module #AnsibleRequires -CSharpUtil should not end in .cs: "%s"' % module_name
                )

        # also accept the legacy #POWERSHELL_COMMON replacer signal
        if not found_requires and REPLACER_WINDOWS not in self.text:
            self.reporter.error(
                path=self.object_path,
                code='missing-module-utils-import-csharp-requirements',
                msg='No Ansible.ModuleUtils or C# Ansible util requirements/imports found'
            )