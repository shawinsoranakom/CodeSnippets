def _scan_module_util(
        self,
        name: str,
        ext: str,
        module_fqn: str | None,
        optional: bool,
    ) -> str | None:
        util_name: str
        util_path: str
        util_data: bytes
        util_fqn: str | None = None

        if name.startswith("Ansible."):
            # Builtin util, or the old role module_utils reference.
            util_name = f"{name}{ext}"

            if util_name in self._util_deps:
                return util_name

            util_path = ps_module_utils_loader.find_plugin(name, ext)
            if not util_path or not os.path.exists(util_path):
                if optional:
                    return None

                raise AnsibleError(f"Could not find imported module util '{name}'")

            with open(util_path, 'rb') as mu_file:
                util_data = mu_file.read()

        else:
            # Collection util, load the package data based on the util import.
            submodules = name.split(".")
            if name.startswith('.'):
                fqn_submodules = (module_fqn or "").split('.')
                for submodule in submodules:
                    if submodule:
                        break
                    del fqn_submodules[-1]

                submodules = fqn_submodules + [s for s in submodules if s]

            util_package = '.'.join(submodules[:-1])
            util_resource_name = f"{submodules[-1]}{ext}"
            util_fqn = f"{util_package}.{submodules[-1]}"
            util_name = f"{util_package}.{util_resource_name}"

            if util_name in self._util_deps:
                return util_name

            try:
                module_util = import_module(util_package)
                util_code = pkgutil.get_data(util_package, util_resource_name)
                if util_code is None:
                    raise ImportError("No package data found")
                util_data = util_code

                # Get the path of the util which is required for coverage collection.
                resource_paths = list(module_util.__path__)
                if len(resource_paths) != 1:
                    # This should never happen with a collection but we are just being defensive about it.
                    raise AnsibleError(f"Internal error: Referenced module_util package '{util_package}' contains 0 "
                                       "or multiple import locations when we only expect 1.")

                util_path = os.path.join(resource_paths[0], util_resource_name)
            except (ImportError, OSError) as err:
                if getattr(err, "errno", errno.ENOENT) == errno.ENOENT:
                    if optional:
                        return None

                    raise AnsibleError(f"Could not find collection imported module support code for '{name}'")

                else:
                    raise

        # This is important to be set before scan_module is called to avoid
        # recursive dependencies.
        self.scripts[util_name] = _ScriptInfo(
            content=util_data,
            path=util_path,
        )

        # It is important this is set before calling scan_module to ensure
        # recursive dependencies don't result in an infinite loop.
        dependencies = self._util_deps[util_name] = set()

        util_deps = self.scan_module(util_data, fqn=util_fqn, powershell=(ext == ".psm1"))
        dependencies.update(util_deps)
        for dep in dependencies:
            if dep_list := self._util_deps.get(dep):
                dependencies.update(dep_list)

        if ext == ".cs":
            # Any C# code requires the AddType.psm1 module to load.
            dependencies.add("Ansible.ModuleUtils.AddType.psm1")
            self._scan_module_util("Ansible.ModuleUtils.AddType", ".psm1", None, False)

        return util_name