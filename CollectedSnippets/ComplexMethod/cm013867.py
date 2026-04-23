def create_resume(
        self,
        idx: int,
        resume_inst: Instruction,
        meta: StackLocalsMetadata,
        resume_codes: list[types.CodeType],
        cg: PyCodegen,
        is_leaf: bool,
        handle_inactive_ctx: bool,
    ) -> tuple[types.CodeType, str]:
        """
        Creates the resume function for the frame corresponding to `self`.

        Expects the TOS to be:
            [frame N cells, ..., frame 1 cells],
            [
                frame N stack + locals,
                ...,
                frame 1 stack + locals
            ]

        Some additional codegen may happen to prepare the frame stack + locals values for the generated resume function:
        - inactive context variables in the stack and locals will be replaced by their types
        - if the frame is a leaf frame, prune dead locals

        Regardless of codegen, the stack will be left in the same state as before.

        Args:
            - idx: depth of this frame: 0 corresponds to the leaf frame (frame N), N-1 to the root frame (frame 1).
            - resume_inst: the instruction that this frame should resume at
            - meta: metadata for this frame returned from OutputGraph.compile_subgraph
            - resume_codes: nested resume code objects generated from previous create_resume calls.
            - cg: codegen object to output to
            - is_leaf: True if `self` corresponds to the leaf frame.
            - handle_inactive_ctx: If True, handles inactive context variables as described above. This is necessary
                iff the resume function is traced
        """
        # Handle inactive context variables.
        # The resume function assumes that context variables are the class, NOT the object.
        # e.g. torch.set_grad_enabled(True) will be reconstructed as torch.set_grad_enabled
        # NOTE: if the unsupported instruction modifies the inactive context variable, it may
        # result in silent incorrectness!
        if handle_inactive_ctx:
            for (j, _), j_orig in zip(meta.stack_ctx_args, meta.stack_ctx_idxes_orig):
                # Replace the stack var with the context class
                ctx = cast(ContextWrappingVariable, self.stack[j_orig])
                # frames[idx][j] = reconstructed_ctx
                cg.append_output(create_dup_top())
                ctx.reconstruct_type(cg)
                cg.extend_output(
                    [
                        *create_swap(2),
                        cg.create_load_const(idx),
                        cg.create_binary_subscr(),
                        cg.create_load_const(j),
                        create_instruction("STORE_SUBSCR"),
                    ]
                )

            for name, _ in meta.locals_ctx_args:
                # Replace the local with the context class
                ctx = cast(ContextWrappingVariable, self.symbolic_locals[name])
                # frames[idx][meta.num_stack +meta.locals_names[name]] = reconstructed_ctx
                cg.append_output(create_dup_top())
                ctx.reconstruct_type(cg)
                cg.extend_output(
                    [
                        *create_swap(2),
                        cg.create_load_const(idx),
                        cg.create_binary_subscr(),
                        cg.create_load_const(meta.num_stack + meta.locals_names[name]),
                        create_instruction("STORE_SUBSCR"),
                    ]
                )

        # If the resume instruction is a jump absolute, then resume
        # at the target instead. This handles the case where we
        # graph break again in a nested function before jump-resuming
        # this frame.
        if is_jump_absolute(resume_inst):
            assert resume_inst.target
            resume_inst = resume_inst.target

        resume_name = unique_id(f"__resume_at_{resume_inst.offset}")

        # More locals may have been pruned in the current/leaf frame
        # after the unsupported instruction (e.g. branch).
        # There should not be any pruning in the other frames since
        # the current instruction there should be a CALL.
        if is_leaf:
            reads = livevars_analysis(self.instructions, resume_inst)
            all_argnames = tuple(
                k
                for k in self.symbolic_locals
                if k in reads and k not in self.cell_and_freevars()
            )
            argnames_null_set = set(meta.locals_null_keys)
            argnames = tuple(k for k in all_argnames if k not in argnames_null_set)
            argnames_null = tuple(k for k in all_argnames if k in argnames_null_set)

            # codegen filter for current frame's locals
            # current stack state: frames
            cg.extend_output(
                [
                    create_dup_top(),
                    cg.create_load_const(idx),
                    cg.create_binary_subscr(),
                    create_dup_top(),
                ]
            )
            for arg in argnames:
                # current stack state: frames, frames[i], *(prev locals), frames[i]
                cg.extend_output(
                    [
                        create_dup_top(),
                        cg.create_load_const(meta.num_stack + meta.locals_names[arg]),
                        cg.create_binary_subscr(),
                        *create_swap(2),
                    ],
                )
            # current stack state: frames, frames[i], *(frame i live locals), frames[i]
            cg.extend_output(
                [
                    create_instruction("POP_TOP"),
                    create_instruction("BUILD_LIST", arg=len(argnames)),
                    *create_swap(2),
                    # frames, frames i live locals, frames[i]
                    *create_binary_slice(meta.num_stack, None, True),
                    # frames[i][num_stack:] = frame i live locals
                ]
            )
            # current stack state: frames
        else:
            argnames = tuple(meta.locals_names.keys())
            argnames_null = tuple(meta.locals_null_keys)

        if sys.version_info < (3, 12):
            assert len(argnames_null) == 0, "variables should not be NULL in < 3.12"

        # compile_subgraph did not codegen any NULLs,
        # so we should not count NullVariables
        stack_len = len(self.stack) - len(meta.stack_null_idxes)

        assert self.current_instruction.offset is not None
        new_code: types.CodeType = ContinueExecutionCache.lookup(
            self.f_code,
            self.lineno,
            self.current_instruction.offset,
            resume_inst.offset,
            # pyre: ignore[missing-attribute]
            tuple(b.target.offset for b in self.block_stack),
            stack_len,
            argnames,
            argnames_null,
            tuple(b.resume_fn() for b in self.block_stack),
            handle_inactive_ctx,
            tuple(meta.stack_ctx_args),
            tuple(meta.locals_ctx_args),
            tuple(meta.stack_null_idxes),
            tuple(resume_codes),
            not self.current_instruction_push,
        )

        # Add original GraphModule context to the resume function to handle
        # the case of a graph break while tracing a GraphModule
        orig_graphmodule_maybe = code_context.get_context(self.f_code).get(
            "orig_graphmodule", lambda: None
        )()
        if orig_graphmodule_maybe is not None:
            code_context.get_context(new_code)["orig_graphmodule"] = weakref.ref(
                orig_graphmodule_maybe
            )

        # add resume function to the global scope
        self.output.install_resume_function_global(
            resume_name, new_code, self.f_globals
        )
        if self.package is not None:
            self.package.add_resume_function(
                new_code, self.f_globals["__name__"], resume_name
            )

        counters["resumes"][new_code.co_name] += 1

        return new_code, resume_name