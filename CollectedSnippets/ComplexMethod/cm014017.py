def _get_stack_values_to_restore(
        self, tx: "InstructionTranslatorBase", stack_pops: int
    ) -> tuple[list[VariableTracker], StackLocalsMetadata]:
        """
        Gets the stack + locals values belonging to tx that need to be restored.

        Also prunes dead tx locals and realizes all VTs in the tx's stack.

        NullVariables in stack/locals will NOT be restored, unless they are the top `stack_pops`
        elements of the stack - it is expected that the next instruction to run will pop the top
        `stack_pops` elements of the stack, so we should codegen NULLs.

        Returns:
            - stack_values: stack and locals values that need to be restored
            - meta: locations of NULLs and ContextWrappingVariables in the stack/locals
                (ignores the top `stack_pops` values on the stack)
        """
        tx.prune_dead_locals()

        stack_values = []
        meta = StackLocalsMetadata()

        def ctx_exit_check(var: VariableTracker) -> None:
            if type.__instancecheck__(variables.WithExitFunctionVariable, var):
                raise AssertionError(
                    "Attempted to reconstruct WithExitFunctionVariable outside the stack"
                )

        # realize any unrealized tensor VTs in case they
        # need to be added to self.nn_modules as attributes
        for i, value in enumerate(tx.stack):
            # Allow lazy constants through for values being returned (top of stack)
            allow_lazy_constant = len(tx.stack) - i <= stack_pops
            variables.LazyVariableTracker.realize_all(
                value, allow_lazy_constant=allow_lazy_constant
            )
            # Do not allow non-stack WithExitFunctionVariable reconstructions
            if not isinstance(value, variables.WithExitFunctionVariable):
                VariableTracker.visit(ctx_exit_check, value)
            # ignore top `stack_pops` values on the stack
            if allow_lazy_constant:
                stack_values.append(value)
                continue
            if isinstance(value, NullVariable):
                meta.stack_null_idxes.append(i)
            else:
                stack_values.append(value)
            if isinstance(value, ContextWrappingVariable):
                target_values = (
                    () if value.target_values is None else tuple(value.target_values)
                )
                # NOTE: track index in stack after NULLs have been removed
                meta.stack_ctx_args.append((len(stack_values) - 1, target_values))
                meta.stack_ctx_idxes_orig.append(i)

        meta.num_stack = len(stack_values)

        cell_and_freevars = set(tx.cellvars() + tx.freevars())

        # NB: Typically (i.e., for graph compile from RETURN_VALUE),
        # symbolic_locals will be empty at this point, as prune_dead_locals
        # will clear out all of symbolic_locals because RETURN_VALUE is the
        # last instruction and no more locals are used.  The fanciness here
        # is only needed for partial graphs.
        # NOTE: All cell and free variables are represented as CellVariable,
        # so checks for NULLs and context managers in the case of codegen'ing resume
        # functions will not be performed on them. This is expected behavior.
        for k, v in tx.symbolic_locals.items():
            # Do not reconstruct WithExitFunctionVariable!
            VariableTracker.visit(ctx_exit_check, v)
            # Note! this explicitly uses .local_name for matching
            # Failure to do so will cause spurious registrations in val_to_names.
            # This will in turn result in spurious variables showing up in the graph.
            # This was very tricky to debug. For an example, dump the graph at call_user_compiler
            # while running test_subgraphs.py
            # Do not include top-frame unmodified locals here - otherwise, the compiled graph may
            # erroneously include them as part of the return. We manually codegen them afterward.
            if (
                isinstance(v.source, LocalSource)
                and v.source.local_name == k
                and tx is self.root_tx
            ):
                continue
            # Do not load cell/free vars
            if k in cell_and_freevars:
                continue
            # Do not load variable if it is NULL.
            if sys.version_info >= (3, 12):
                # NOTE: do not use isinstance, since it realizes lazy VT's
                # Continuation function will load the NULL for v.
                if type.__instancecheck__(NullVariable, v):
                    meta.locals_null_keys.append(k)
                    continue
            else:
                # A variable should never be NULL in < 3.12
                assert not type.__instancecheck__(NullVariable, v)
            meta.locals_names[k] = len(meta.locals_names)
            if isinstance(v, ContextWrappingVariable):
                target_values = (
                    () if v.target_values is None else tuple(v.target_values)
                )
                meta.locals_ctx_args.append((k, target_values))
            stack_values.append(v)

        return stack_values, meta