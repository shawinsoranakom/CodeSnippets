def _dispatch_modules(self, redirected_call_indices, consts_targets):
        """For a module whose call signatures are preserved, replace
        multiple modules corresponding to multiple calls to that module
        with a single dispatcher module that tracks which module to call.
        """

        # for each fqn whose module call signature is preserved,
        # map that fqn to a list of called modules
        called_modules = defaultdict(list)
        for entry in self.module_call_graph:
            if entry.fqn and entry.signature:
                # some modules were removed and their fqns redirected to other
                # fqns during deduplication
                fqn = entry.fqn
                mod = _get_attr(self, redirected_call_indices.get(fqn, fqn))
                base, idx = fqn.split("@") if "@" in fqn else [fqn, "0"]
                called_modules[base].append((int(idx), mod))

        attrs_map = defaultdict(set)
        for target in consts_targets:
            if "." in target:
                orig_fqn, name = target.rsplit(".", 1)
                attrs_map[orig_fqn].add(name)
            else:
                attrs_map[""].add(target)

        # replace multiple call modules with a single dispatcher module
        for orig_fqn, indexed_call_modules in called_modules.items():
            call_modules = [mod for _, mod in sorted(indexed_call_modules)]
            if len(call_modules) > 1:
                for i in range(len(call_modules)):
                    fqn = _call_name(orig_fqn, i + 1)
                    if fqn not in redirected_call_indices:
                        *prefix, name = fqn.split(".")
                        _get_attr_via_attr_list(self, prefix)._modules.pop(name)
                self.set_submodule(
                    orig_fqn,
                    InterpreterModuleDispatcher(attrs_map[orig_fqn], call_modules),
                )

        # elide call indices in call modules because they are
        # tracked automatically inside the dispatcher module
        def elide_call_indices(prefix, graph):
            for node in graph.nodes:
                if node.op == "call_module":
                    fqn = node.target.split("@")[0]
                    path = f"{prefix}.{fqn}" if prefix else fqn
                    if path in called_modules:
                        node.target = fqn

        for fqn, mod in self.named_modules(remove_duplicate=False):
            if hasattr(mod, "graph"):
                elide_call_indices(fqn, mod.graph)
            elif hasattr(mod, "_call_modules"):
                for mod_ in mod._call_modules:
                    if not hasattr(mod_, "graph"):
                        raise AssertionError(
                            f"expected mod_ to have 'graph' attribute, got {type(mod_)}"
                        )
                    elide_call_indices(fqn, mod_.graph)