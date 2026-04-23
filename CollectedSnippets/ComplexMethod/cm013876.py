def __init__(
        self,
        instructions: list[Instruction],
        f_code: types.CodeType,
        f_locals: dict[str, Any],
        f_globals: dict[str, Any],
        f_builtins: dict[str, Any],
        closure: tuple[Any, ...] | None,
        torch_function_mode_stack: Any,
        code_options: dict[str, Any],
        compiler_fn: Any,
        one_graph: bool,
        export: bool,
        export_constraints: Any,
        frame_state: Any,
        speculation_log: SpeculationLog,
        exn_vt_stack: ExceptionStack,
        distributed_state: DistributedState | None,
        package: CompilePackage | None,
    ) -> None:
        _step_logger()(
            logging.INFO,
            f"torchdynamo start tracing {f_code.co_name} {code_options['co_filename']}:{code_options['co_firstlineno']}",
        )
        super().__init__(
            output=OutputGraph(
                code_options,
                compiler_fn,
                self,
                export,
                export_constraints,
                frame_state,
                local_scope=f_locals,
                global_scope=f_globals,
                f_code=f_code,
                torch_function_mode_stack=torch_function_mode_stack,
                one_graph=one_graph,
                package=package,
            ),
            instructions=instructions,
            f_locals=f_locals,
            f_globals=f_globals,
            f_builtins=f_builtins,
            closure=closure,
            code_options=code_options,
            symbolic_locals={},  # set below
            # A global var is inserted only after a STORE_GLOBAL happens to it
            symbolic_globals={},
            symbolic_torch_function_state=None,  # type: ignore[arg-type] # set below
            symbolic_stream_state=None,  # type: ignore[arg-type] # set below
            f_code=f_code,
            export=export,
            inline_depth=0,
            speculation_log=speculation_log,
            exn_vt_stack=exn_vt_stack,
            distributed_state=distributed_state,
            package=package,
        )

        self._throw_if_in_functorch()

        # as soon as we create the tracing context we should keep it active, so any calls
        # into dynamo apis can rely on finding it
        with tracing(self.output.tracing_context), self.set_current_tx():
            self.one_graph: bool = one_graph
            self.export = export
            if self.export:
                assert self.one_graph, (
                    "Export without one graph - something has gone wrong."
                )

            self.symbolic_locals = {}
            # Populate `symbolic_locals` with non-cell variables.
            cell_and_freevars: set[str] = set(self.cell_and_freevars())

            dynamism = code_context.get_context(f_code).get("dynamism", None)
            for name, value in f_locals.items():
                if name not in cell_and_freevars:
                    local_dynamism = None
                    if dynamism:
                        local_dynamism = frozenset(dynamism.get(name, {}).items())
                    var = LazyVariableTracker.create(
                        value,
                        LocalSource(
                            name,
                            is_input=True,
                            dynamism=local_dynamism,
                        ),
                    )
                    self.symbolic_locals[name] = var

            # Populate `symbolic_locals` with cells created by this frame,
            # effectively implementing the `MAKE_CELL` instructions.
            side_effects = self.output.side_effects
            for name in self.cellvars():
                if name in f_locals:
                    # This models cells that are also function inputs.
                    value = f_locals[name]
                    # NOTE: root frame inputs that are captured by a nested
                    # function become special cell objects -- they exist in
                    # `f_locals` as contents of the cells, rather than the cells
                    # objects themselves.
                    #
                    # In Dynamo, we choose to represent such input cell objects
                    # as newly created (rather than pre-existing) cell objects,
                    # because
                    #
                    # 1. The reason for representing a pre-existing cell object
                    # is to emit guard or codegen mutations. However, local
                    # cells should never be used for guards. Moreover, at this
                    # point these input cell objects should've never been
                    # accessed by anyone else, since Dynamo intercepts the frame
                    # right after its evaluation starts, i.e., right after these
                    # cell objects are created. So they should have no external
                    # reference, meaning no mutation needs to be propagated.
                    #
                    # 2. This conveniently allows codegen to prune away
                    # mutations to these cells, unless they escape the frame.
                    contents_source = LocalSource(
                        name,
                        is_input=True,
                        is_derefed_cell_contents=True,
                    )
                    contents_var: VariableTracker = LazyVariableTracker.create(
                        value, contents_source
                    )
                    cell_var = side_effects.track_cell_new()
                    side_effects.store_cell(cell_var, contents_var)
                else:
                    cell_var = side_effects.track_cell_new()
                cell_var.local_name = name  # type: ignore[attr-defined]
                self.symbolic_locals[name] = cell_var

            # Populate `symbolic_locals` with cells captured by this frame,
            # effectively implementing the `COPY_FREE_VARS` instruction.
            assert closure is not None
            for name, cell in zip(self.freevars(), closure):
                cell_source = LocalCellSource(name)
                contents_source = LocalSource(name, is_derefed_cell_contents=True)
                try:
                    contents_var = LazyVariableTracker.create(
                        cell.cell_contents, contents_source
                    )
                except ValueError:
                    # Cell has not yet been assigned
                    contents_var = variables.DeletedVariable()
                cell_var = side_effects.track_cell_existing(
                    cell_source, cell, contents_var
                )
                cell_var.local_name = name  # type: ignore[attr-defined]
                self.symbolic_locals[name] = cell_var

            self.symbolic_torch_function_state = SymbolicTorchFunctionState(
                torch_function_mode_stack
            )

            self.symbolic_stream_state = SymbolicStreamState()

            if export:
                # export gets confused if we never realize unused inputs
                # in export mode just eagerly realize everything
                self.symbolic_locals = variables.LazyVariableTracker.realize_all(
                    self.symbolic_locals
                )