def run(
        self,
        *args: Any,
        initial_env: dict[Node, Any] | None = None,
        enable_io_processing: bool = True,
    ) -> Any:
        """
        Run `module` via interpretation and return the result.

        Args:
            *args: The arguments to the Module to run, in positional order
            initial_env (Optional[Dict[Node, Any]]): An optional starting environment for execution.
                This is a dict mapping `Node` to any value. This can be used, for example, to
                pre-populate results for certain `Nodes` so as to do only partial evaluation within
                the interpreter.
            enable_io_processing (bool): If true, we process the inputs and outputs with graph's process_inputs and
                process_outputs function first before using them.

        Returns:
            Any: The value returned from executing the Module
        """
        self.env = initial_env if initial_env is not None else {}

        # Positional function args are consumed left-to-right by
        # `placeholder` nodes. Use an iterator to keep track of
        # position and extract those values.
        if enable_io_processing:
            args = self.graph.process_inputs(*args)
        self.args_iter: Iterator[Any] = iter(args)
        pbar = tqdm(
            total=len(self.graph.nodes),
            desc=f"{self.name}: {str(list(self.graph.nodes)) if config.verbose_progress else ''}",
            initial=0,
            position=0,
            leave=True,
            disable=config.disable_progress,
            delay=0,
        )

        for node in self.graph.nodes:
            pbar.update(1)
            if node in self.env:
                # Short circuit if we have this value. This could
                # be used, for example, for partial evaluation
                # where the caller has pre-populated `env` with
                # values for a subset of the program.
                continue

            try:
                self.env[node] = self.run_node(node)
            except Exception as e:
                if self.extra_traceback:
                    msg = f"While executing {node.format_node()}"
                    msg = f"{e.args[0]}\n\n{msg}" if e.args else str(msg)
                    msg += f"\nOriginal traceback:\n{node.stack_trace}"
                    if (
                        isinstance(self.module, GraphModule)
                        and self.module.graph is not None
                        and isinstance(self.module.graph, torch.fx.Graph)
                    ):
                        trace_structured(
                            "artifact",
                            metadata_fn=lambda: {
                                "name": "fx_interpreter_error",
                                "encoding": "string",
                            },
                            payload_fn=lambda: (
                                f"{msg}\nGraphModule: "
                                f"{self.module.print_readable(print_output=False, include_stride=True)}"  # type: ignore[operator]
                            ),
                        )

                    msg += "\nUse tlparse to see full graph. "
                    msg += "(https://github.com/pytorch/tlparse?tab=readme-ov-file#tlparse-parse-structured-pt2-logs)"
                    e.args = (msg,) + e.args[1:]
                    if isinstance(e, KeyError):
                        raise RuntimeError(*e.args) from e
                raise

            if self.garbage_collect_values:
                for to_delete in self.user_to_last_uses.get(node, []):
                    del self.env[to_delete]

            if node.op == "output":
                output_val = self.env[node]
                return (
                    self.graph.process_outputs(output_val)
                    if enable_io_processing
                    else output_val
                )