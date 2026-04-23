def compile_subgraph(
        self,
        tx: "InstructionTranslatorBase",
        reason: GraphCompileReason,
        stack_pops: int = 0,
    ) -> list[StackLocalsMetadata]:
        """
        Compiles the current subgraph, with inputs w.r.t. self.root_tx, and codegens:
            - Call the compiled subgraph
            - Apply side effects
            - Codegen stack and locals
            - Store the locals

        Python does not allow NULL to be an arg to a function, so we do not codegen NULLs on the stack,
        unless the value is one of the top `stack_pops` values on the stack (these values are expected to be
        popped immediately after this generated code. The prologue of the resume function is expected to restore
        any dropped NULLs.

        Returns stack indices and locals keys where we dropped NULLs, and where we found inactive context manager objects.
        """

        assert self.root_tx is not None

        if not config.nested_graph_breaks:
            # expect to only compile 1 frame
            assert self.root_tx is tx

        # bytecode tracing has finished. Pop the context manager for dynamo_timed
        self.mark_bytecode_tracing_stop()

        self.compile_subgraph_reason = reason
        self.should_exit = True

        log.debug("COMPILING GRAPH due to %s", reason)

        # prefix instructions (Python 3.11+)
        prefix_insts: list[Instruction] = []
        if sys.version_info >= (3, 11):
            for inst in self.root_tx.prefix_insts:
                if inst.opname == "COPY_FREE_VARS":
                    prefix_insts.append(
                        create_instruction(
                            "COPY_FREE_VARS",
                            arg=len(self.root_tx.code_options["co_freevars"]),
                        )
                    )
                else:
                    prefix_insts.append(copy.copy(inst))

        # stack values and restore vars for each frame are pushed in reverse order
        # i.e. last element corresponds to root frame (1),
        # first element corresponds to current frame (N)
        all_stack_values = []
        # pyrefly: ignore [implicit-any]
        all_stack_locals_metas = []
        cur_tx: InstructionTranslatorBase | None = tx
        while cur_tx is not None:
            # this should have been checked by the caller
            assert all(block.can_restore() for block in cur_tx.block_stack)

            stack_values, meta = self._get_stack_values_to_restore(
                cur_tx, stack_pops if cur_tx is tx else 0
            )
            all_stack_values.append(stack_values)
            all_stack_locals_metas.append(meta)

            # Exit from all context manager variables to make sure global state is restored
            for block in reversed(cur_tx.block_stack):
                block.exit(cur_tx, is_graph_break=reason.graph_break)

            cur_tx = cur_tx.parent

        # "Garbage collect the heap".
        self.side_effects.prune_dead_object_new(tx)

        self.add_output_instructions(prefix_insts)

        if self._emit_debugger_breakpoint:
            from .bytecode_transformation import create_breakpoint

            self.add_output_instructions(create_breakpoint())
            self._emit_debugger_breakpoint = False

        assert not (self.pregraph_bytecode and self.export), (
            "export does not support pregraph_bytecode"
        )
        self.add_output_instructions(self.pregraph_bytecode)

        alias_insts, overridden_sources = self.handle_aliases_for_stolen_lists(
            self.root_tx
        )
        self.add_output_instructions(alias_insts)

        self.cleanup_graph()

        # Use nn.Module "proxies" in the constructed GraphModule so that
        # the resulting GM does not hold additional strong references to the original modules.
        # This prevents a strong ref cycle where Dynamo created code holds on to references
        # to modules that also have Dynamo code cache invalidation checks.
        # When cache invalidation runs, the generated GM will be invalidated, which also deletes
        # the proxies.
        nn_modules_proxies = {
            name: nn_module_proxy(mod) for name, mod in self.nn_modules.items()
        }
        root = FakeRootModule(nn_modules_proxies)

        from .decorators import disable

        # to handle random calls
        if len(self.random_calls) > 0:
            random_calls_instructions = []
            self.random_values_var = self.new_var("random_values")
            rand_fn = disable(
                _get_gen_rand_values_fn(self.random_calls),
                reason="do not trace into Dynamo rng recovery function",
            )
            rand_fn_name = self.install_global("__gen_rand_values", rand_fn)
            codegen = PyCodegen(
                self.root_tx, root, overridden_sources=overridden_sources
            )
            random_calls_instructions.extend(
                codegen.load_function_name(rand_fn_name, True)
            )
            random_calls_instructions.extend(create_call_function(0, False))
            random_calls_instructions.append(
                codegen.create_store(self.random_values_var),
            )
            self.add_output_instructions(random_calls_instructions)

        # Codegen stack convention before the unsupported instruction
        # NOTE: in these comment blocks, "locals" EXCLUDE free and cell vars.
        # NOTE: stack/locals/cells must be codegen'd BEFORE the unsupported instruction, since the latter
        # can arbitrarily mutate the former.
        # [frame N cells, .., frame 1 cells],
        # [
        #   frame N locals,
        #   frame N-1 stack + locals,
        #   ...,
        #   frame 1 stack + locals,
        # ], frame N stack

        # see symbolic_convert.py for
        # codegen stack convention after the unsupported instruction
        # NOTE: cells will be loaded into continuation functions directly by symbolic_convert

        # this determines the order that values are codegen'd to the stack
        stack_values_flat = [val for vals in all_stack_values for val in vals]
        stored_graph_output_var = False
        graph_output_var = None

        # call compiled fx graph and codegen all values - stack and locals
        if (
            self.root_tx is tx  # single frame
            and stack_values_flat
            and all(
                not isinstance(
                    v,
                    (
                        UnspecializedPythonVariable,
                        NumpyNdarrayVariable,
                        TensorWithTFOverrideVariable,
                    ),
                )
                and not (isinstance(v, SymNodeVariable) and v.python_type() is float)
                for v in stack_values_flat
            )
            and all(x.is_tensor() for x in stack_values_flat)
            and len(set(stack_values_flat)) == len(stack_values_flat)
            and self.side_effects.is_empty()
            and not tx.debug_locals
            and not self.backward_state
            and not all_stack_locals_metas[-1].stack_null_idxes
            and not all_stack_locals_metas[-1].locals_null_keys
        ):
            # optimization to generate better code in a common case

            # codegen cells
            # no side effects, so no new cells created - no need to call side_effects.codegen_save_tempvars
            cell_cg = PyCodegen(self.root_tx)
            self.codegen_cells(tx, cell_cg)
            self.add_output_instructions(
                [
                    # load in reverse since UNPACK_SEQUENCE will reverse
                    *self.compile_and_call_fx_graph(
                        tx, list(reversed(stack_values_flat)), root
                    ),
                    *cell_cg.get_instructions(),
                    *create_swap(2),
                    create_instruction("UNPACK_SEQUENCE", arg=len(stack_values_flat)),
                ]
            )
            # function output will be moved to the correct places below
        else:
            graph_output_var = self.new_var("graph_out")
            # load stack values in a flat manner - we will codegen bytecode to place them correctly
            # according to our convention above
            pass1 = PyCodegen(
                self.root_tx,
                root,
                graph_output_var,
                overridden_sources=overridden_sources,
            )
            self.codegen_suffix(tx, stack_values_flat, pass1, False)

            # Use `pass1.uses` to selectively cache multi-user variables into a
            # temporary local source. This (a). speeds up loading VTs with long
            # chained source, and (b). avoids redundantly saving single-user VT
            # into a temporary local.
            tempvars = {}  # type: ignore[var-annotated]
            for val, count in pass1.uses.items():
                # If it's already a local source, no need to cache it
                if count > 1 and not istype(val, (SyntheticLocalSource, LocalSource)):
                    tempvars[val] = None
            pass2 = PyCodegen(
                self.root_tx,
                root,
                graph_output_var,
                tempvars=tempvars,
                overridden_sources=overridden_sources,
            )
            self.codegen_suffix(tx, stack_values_flat, pass2, True)

            if (
                torch._dynamo.config.log_graph_in_out_metadata
                and stack_values_flat
                and len(stack_values_flat) == 1
            ):
                vt = stack_values_flat[0]
                if (
                    isinstance(vt, torch._dynamo.variables.NamedTupleVariable)
                    and vt.tuple_cls
                    is torch._dynamo.functional_export.ExportTracerOutput
                ):
                    flat_returns = vt.items[0]
                    out_spec = vt.items[1]
                    assert isinstance(
                        flat_returns, torch._dynamo.variables.ListVariable
                    )

                    vt_to_graph_out_idx: dict[VariableTracker, int] = {}
                    for value in pass2.graph_outputs.values():
                        assert isinstance(value, torch._dynamo.codegen.GraphOutputEntry)
                        variable: VariableTracker = value.variable
                        vt_to_graph_out_idx[variable] = value.index

                    for idx, vt in enumerate(flat_returns.items):
                        if vt in vt_to_graph_out_idx:
                            self.export_metadata.output_return_type[idx] = (
                                "graph_out",
                                vt_to_graph_out_idx[vt],
                            )
                        elif (
                            vt.source is not None
                            and (source := getattr(vt.source, "base", None))  # type: ignore[assignment]
                            and getattr(source, "is_input", False)
                        ):
                            self.export_metadata.output_return_type[idx] = (
                                "input",
                                vt.source,
                            )
                        elif vt.is_python_constant():
                            self.export_metadata.output_return_type[idx] = (
                                "constant",
                                vt.as_python_constant(),
                            )
                        else:
                            raise AssertionError(
                                f"Encountered unrecognized type {vt} at output {idx}"
                            )
                    try:
                        self.export_metadata.out_spec = out_spec.as_python_constant()
                    except ClosureConversionError as e:
                        unimplemented(
                            gb_type="nested function with non-constructible closure in output",
                            context=f"as_python_constant for out_spec {out_spec}",
                            explanation=(
                                "Cannot return a nested function with closure from a compiled function. "
                                "Dynamo failed to construct the function defined in the compiled region with closure objects."
                            ),
                            hints=[
                                "Define the function at module scope instead of inside another function ",
                                "Ensure that all closure variables are constants.",
                            ],
                            from_exc=e,
                        )

            output = []
            if count_calls(self.graph) != 0 or len(pass2.graph_outputs) != 0:
                output.extend(
                    self.compile_and_call_fx_graph(tx, pass2.graph_output_vars(), root)
                )

                if len(pass2.graph_outputs) != 0:
                    output.append(pass2.create_store(graph_output_var))
                    stored_graph_output_var = True
                else:
                    output.append(create_instruction("POP_TOP"))
            else:
                # NB: Important to run compiler collective even when there is
                # a graph break
                self.run_compiler_collective()
            self.add_output_instructions(output + pass2.get_instructions())

        # store all stack and locals for each frame
        # current state of the stack:
        # all cells,
        # *(frame N stack), *(frame N locals),
        # ...,
        # *(frame 1 stack), *(frame 1 locals)

        self.add_output_instructions(
            [
                create_instruction(
                    "BUILD_LIST",
                    arg=len(stack_values_flat) - all_stack_locals_metas[0].num_stack,
                ),
            ]
        )

        # current state of the stack:
        # all cells,
        # *(frame N stack), [
        #     *(frame N locals),
        #     *(frame N-1 stack), *(frame N-1 locals),
        #     ...
        #     *(frame 1 stack), *(frame 1 locals),
        # ]
        # iterate current frame (N) to root frame (1)
        # sliding window over frame stack/locals
        start_idx = 0
        end_idx = 0
        for i, meta in enumerate(all_stack_locals_metas):
            # do not pack frame N's stack into the value list
            n_vals = len(meta.locals_names)
            if i != 0:
                n_vals += meta.num_stack
            if n_vals == 0:
                self.add_output_instructions(
                    [
                        create_instruction("BUILD_LIST", arg=0),
                        *create_swap(2),
                    ]
                )
                # [], stack_values_flat
            else:
                end_idx += n_vals
                self.add_output_instructions(
                    [
                        create_dup_top(),
                        *create_binary_slice(start_idx, end_idx),
                        *create_swap(2),
                    ]
                )
                start_idx += n_vals
                # stack_values_flat[x:y], stack_values_flat

            # add root frame's unmodified locals here
            if i == len(all_stack_locals_metas) - 1:
                root_cg = PyCodegen(self.root_tx)
                unmodified_locals_names: dict[str, int] = {}
                for k, v in self.root_tx.symbolic_locals.items():
                    if isinstance(v.source, LocalSource) and v.source.local_name == k:
                        root_cg.append_output(root_cg.create_load(k))
                        unmodified_locals_names[k] = len(meta.locals_names) + len(
                            unmodified_locals_names
                        )
                self.add_output_instructions(
                    root_cg.get_instructions()
                    + [
                        create_instruction(
                            "BUILD_LIST", arg=len(unmodified_locals_names)
                        ),
                        # arg=2 because we already swapped the locals list back
                        create_instruction("LIST_EXTEND", arg=2),
                    ]
                )
                meta.locals_names.update(unmodified_locals_names)

            # *(frame N stack), metas[0] stack + locals, ..., metas[i] stack + locals, stack_values_flat

        # current state of the stack:
        # all cells,
        # *(frame N stack),
        # frame N locals,
        # frame N-1 stack, frame N-1 locals,
        # ...
        # frame 1 stack, frame 1 locals,
        # stack_values_flat
        #

        self.add_output_instructions(
            [
                create_instruction("POP_TOP"),
                create_instruction("BUILD_LIST", arg=len(all_stack_locals_metas)),
                *create_rot_n(all_stack_locals_metas[0].num_stack + 1),
            ]
        )

        # final state of the stack before running the unsupported bytecode:
        # all cells,
        # [
        #   [frame N locals],
        #   [frame N-1 stack + locals],
        #   ...,
        #   [frame 1 stack + locals],
        # ], *(frame N stack)

        if graph_output_var and stored_graph_output_var:
            self.add_output_instructions(
                [create_instruction("DELETE_FAST", argval=graph_output_var)]
            )

        if torch._dynamo.config.side_effect_replay_policy in ["warn", "error"]:
            side_effect_refs = self.get_replayed_side_effect_source_refs(
                populate_export_metadata=True
            )
            if side_effect_refs:
                if torch._dynamo.config.side_effect_replay_policy == "warn":
                    warnings.warn(
                        f"While compiling, we found certain side effects happened in the model.forward. "
                        f"Here are the list of potential sources you can double check: {side_effect_refs}"
                    )
                else:
                    raise RuntimeError(
                        f"While compiling, we found certain side effects happened in the model.forward. "
                        f"Here are the list of potential sources you can double check: {side_effect_refs}"
                    )

        return all_stack_locals_metas