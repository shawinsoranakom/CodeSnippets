def __init__(self, args: TestConfig) -> None:
        self.args = args
        self.integration_all_target = get_integration_all_target(self.args)

        self.integration_targets = list(walk_integration_targets())
        self.module_targets = list(walk_module_targets())
        self.compile_targets = list(walk_compile_targets())
        self.units_targets = list(walk_units_targets())
        self.sanity_targets = list(walk_sanity_targets())
        self.powershell_targets = [target for target in self.sanity_targets if os.path.splitext(target.path)[1] in ('.ps1', '.psm1')]
        self.csharp_targets = [target for target in self.sanity_targets if os.path.splitext(target.path)[1] == '.cs']

        self.units_modules = set(target.module for target in self.units_targets if target.module)
        self.units_paths = set(a for target in self.units_targets for a in target.aliases)
        self.sanity_paths = set(target.path for target in self.sanity_targets)

        self.module_names_by_path = dict((target.path, target.module) for target in self.module_targets)
        self.integration_targets_by_name = dict((target.name, target) for target in self.integration_targets)
        self.integration_targets_by_alias = dict((a, target) for target in self.integration_targets for a in target.aliases)

        self.posix_integration_by_module = dict((m, target.name) for target in self.integration_targets
                                                if 'posix/' in target.aliases for m in target.modules)
        self.windows_integration_by_module = dict((m, target.name) for target in self.integration_targets
                                                  if 'windows/' in target.aliases for m in target.modules)
        self.network_integration_by_module = dict((m, target.name) for target in self.integration_targets
                                                  if 'network/' in target.aliases for m in target.modules)

        self.prefixes = load_integration_prefixes()
        self.integration_dependencies = analyze_integration_target_dependencies(self.integration_targets)

        self.python_module_utils_imports: dict[str, set[str]] = {}  # populated on first use to reduce overhead when not needed
        self.powershell_module_utils_imports: dict[str, set[str]] = {}  # populated on first use to reduce overhead when not needed
        self.csharp_module_utils_imports: dict[str, set[str]] = {}  # populated on first use to reduce overhead when not needed

        self.paths_to_dependent_targets: dict[str, set[IntegrationTarget]] = {}

        for target in self.integration_targets:
            for path in target.needs_file:
                if path not in self.paths_to_dependent_targets:
                    self.paths_to_dependent_targets[path] = set()

                self.paths_to_dependent_targets[path].add(target)