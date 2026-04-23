def prune(self) -> None:
        r"""
        This function will FX symbolically trace the model and then find instances of the patterns
        defined in self.patterns (by default SUPPORTED_STRUCTURED_PRUNING_PATTERNS ).

        For each pattern, it will apply to corresponding conversion function, which will modify the output
        and input size expected by the modules within the pattern
        """

        self.traced = symbolic_trace(self.model)
        modules = dict(self.traced.named_modules())

        # Right now we check for matches simply by iterating across all the patterns
        # if this is slow we can store patterns in a trie-structure and modify this code for faster lookup
        for node in self.traced.graph.nodes:
            for pattern, convert_fn in self.patterns.items():
                matched = apply_match(modules, pattern, node, [])
                if matched is None:
                    continue

                # pyrefly: ignore [no-matching-overload]
                first_module = modules.get(node.target)
                # check if first module exists and has appropriate parameterization, otherwise skip
                if (
                    first_module is not None
                    and parametrize.is_parametrized(first_module)
                    and module_contains_param(first_module, FakeStructuredSparsity)
                ):
                    convert_block = []
                    for node in matched:
                        if node.op == "call_module":
                            convert_block.append(modules.get(node.target))
                        elif node.op == "call_function":
                            convert_block.append(node.target)
                    convert_fn(*convert_block)

        for module in self.traced.modules():
            if module_contains_param(module, FakeStructuredSparsity):
                raise Exception(  # noqa: TRY002
                    f"Error: {module} still contains FakeStructuredSparsity parametrizations!"
                )

        self.traced.graph.lint()
        self.traced.recompile()
        return self.traced