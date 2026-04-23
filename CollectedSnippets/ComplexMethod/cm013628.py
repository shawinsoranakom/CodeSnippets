def __call__(self, module: nn.Module) -> PassResult:
        """
        Runs a list of passes in the order based on `self.passes` on the given
        graph module. Each time a pass is run, checks and linting will be run on
        the graph module if `run_checks_after_each_pass` is set.

        If the module is a graph module, we will run the list of passes until
        the graph stops changing, or until `steps` number of times.
        """
        # Order the passes based on the constraints
        if not self._validated:
            self.solve_constraints()

        # Check graph invariants
        self.check(module)

        # Run the set of passes `steps` number of times or until the graph stops
        # changing
        overall_modified = False
        for _ in range(self.steps):
            modified = False

            # Run the set of passes on the graph module
            for i, fn in enumerate(self.passes):
                fn_name = fn.__name__ if inspect.isfunction(fn) else type(fn).__name__
                logger.debug("Running pass '%s'", fn_name)

                try:
                    res = fn(module)

                    if not isinstance(res, PassResult) and not hasattr(
                        res, "graph_module"
                    ):
                        raise TypeError(
                            f"The result of the pass {fn_name} should be type PassResult."
                            + "Please wrap it with pass_result_wrapper()"
                        )
                    # pyrefly: ignore[missing-attribute]
                    module = res.graph_module
                    # pyrefly: ignore[missing-attribute]
                    modified = modified or res.modified

                    if isinstance(module, GraphModule):
                        logger.debug("Graph after pass '%s': %s", fn_name, module.graph)
                        module.recompile()

                    # Check graph invariants
                    if self.run_checks_after_each_pass:
                        self.check(module)

                except Exception as e:
                    prev_pass_names = [
                        p.__name__ if inspect.isfunction(p) else type(p).__name__
                        for p in self.passes[:i]
                    ]
                    msg = f"An error occurred when running the '{fn_name}' pass after the following passes: {prev_pass_names}"
                    raise Exception(msg) from e  # noqa: TRY002

            # If the graph no longer changes, then we can stop running these passes
            overall_modified = overall_modified or modified
            if not modified:
                break

        return PassResult(module, overall_modified)