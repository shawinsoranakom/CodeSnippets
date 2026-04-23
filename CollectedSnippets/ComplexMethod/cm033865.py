def scan_module(
        self,
        module_data: bytes,
        fqn: str | None = None,
        powershell: bool = True,
    ) -> set[str]:
        lines = module_data.split(b'\n')
        module_utils: set[tuple[str, str, bool]] = set()

        if fqn and fqn.startswith("ansible_collections."):
            submodules = fqn.split('.')
            collection_name = '.'.join(submodules[:3])

            collection_hashlist = _get_powershell_signed_hashlist(collection_name)
            if collection_hashlist and collection_hashlist.path not in self.signed_hashlist:
                self.signed_hashlist.add(collection_hashlist.path)
                self.scripts[collection_hashlist.path] = collection_hashlist

        if powershell:
            checks = [
                # PS module contains '#Requires -Module Ansible.ModuleUtils.*'
                # PS module contains '#AnsibleRequires -Powershell Ansible.*' (or collections module_utils ref)
                (self._re_ps_module, ".psm1"),
                # PS module contains '#AnsibleRequires -CSharpUtil Ansible.*' (or collections module_utils ref)
                (self._re_cs_in_ps_module, ".cs"),
            ]
        else:
            checks = [
                # CS module contains 'using Ansible.*;' or 'using ansible_collections.ns.coll.plugins.module_utils.*;'
                (self._re_cs_module, ".cs"),
            ]

        for line in lines:
            for patterns, util_extension in checks:
                for pattern in patterns:
                    match = pattern.match(line)
                    if match:
                        # tolerate windows line endings by stripping any remaining
                        # newline chars
                        module_util_name = to_text(match.group(1).rstrip())
                        match_dict = match.groupdict()
                        optional = match_dict.get('optional', None) is not None
                        module_utils.add((module_util_name, util_extension, optional))
                        break

            if not powershell:
                continue

            if ps_version_match := self._re_ps_version.match(line):
                self._parse_version_match(ps_version_match, "ps_version")

            if os_version_match := self._re_os_version.match(line):
                self._parse_version_match(os_version_match, "os_version")

            # once become is set, no need to keep on checking recursively
            if not self.become and self._re_become.match(line):
                self.become = True

        dependencies: set[str] = set()
        for name, ext, optional in set(module_utils):
            util_name = self._scan_module_util(name, ext, fqn, optional)
            if util_name:
                dependencies.add(util_name)
                util_deps = self._util_deps[util_name]
                dependencies.update(util_deps)

        return dependencies