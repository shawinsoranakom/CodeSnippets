def step_graph_break(self, continue_inst: Instruction) -> None:
        # generate code from checkpoint
        assert not self.output.output_instructions
        assert self.current_speculation is not None
        # NOTE: adding an assert here since it seems like the only place
        # where we call step_graph_break right now is when the stack is empty,
        # so let's enforce that for now.
        assert not self.stack
        # NOTE: if we support non-empty self.stack in the future, the `stack_pops` argument
        # below should be set to the stack length to ensure that the stack is codegen'd
        # for the rest of the function.
        log.debug("step triggered compile")
        all_stack_locals_metadata = self.output.compile_subgraph(
            self,
            reason=GraphCompileReason("step_unsupported", [self.frame_summary()]),
        )
        # current frame state
        # cells,
        # [
        #   frame N locals,
        #   frame N-1 stack + locals,
        #   ...,
        #   frame 1 stack + locals,
        # ],
        if self.parent:
            from .eval_frame import skip_code

            # nested graph break
            assert config.nested_graph_breaks
            cg = PyCodegen(self.output.root_tx)

            # codegen cells and frame values only for frame N
            cg.extend_output(
                [
                    *create_copy(2),
                    cg.create_load_const(0),
                    cg.create_binary_subscr(),
                    create_instruction("BUILD_LIST", arg=1),
                    *create_copy(2),
                    cg.create_load_const(0),
                    cg.create_binary_subscr(),
                    create_instruction("BUILD_LIST", arg=1),
                ]
            )
            # No need to fix stack, since stack is assumed to be empty here.
            # Do NOT handle_inactive_ctx because we will be skipping this resume code.
            leaf_resume_code, leaf_resume_name = self.create_resume(
                0, continue_inst, all_stack_locals_metadata[0], [], cg, True, False
            )
            skip_code(leaf_resume_code)

            cleanup: list[Instruction] = []
            _reconstruct_block_stack(self.parent, cg, cleanup)

            # current frame state
            # cells,
            # [
            #   frame N locals,
            #   frame N-1 stack + locals,
            #   ...,
            #   frame 1 stack + locals,
            # ], [frame N cells], [frame N locals],
            self.codegen_call_resume([leaf_resume_code], [leaf_resume_name], cg)

            cg.extend_output(cleanup)

            # current frame state
            # cells,
            # [
            #   frame N locals,
            #   frame N-1 stack + locals,
            #   ...,
            #   frame 1 stack + locals,
            # ], leaf_resume result

            # pop frame N cells and locals
            cg.extend_output(
                [
                    *create_copy(2),
                    cg.create_load_const(0),
                    create_instruction("DELETE_SUBSCR"),
                    *create_copy(3),
                    cg.create_load_const(0),
                    create_instruction("DELETE_SUBSCR"),
                ]
            )

            # current frame state
            # cells, frame_values, leaf_resume result
            # extract frame N-1 stack
            num_stack = all_stack_locals_metadata[1].num_stack
            cg.extend_output(
                [
                    *create_copy(2),
                    cg.create_load_const(0),
                    cg.create_binary_subscr(),
                    *create_binary_slice(0, num_stack),
                ]
            )

            # current frame state
            # cells, frame_values, leaf_resume result, frame N-1 stack
            # add the leaf_resume result to frame N-1 stack
            cg.extend_output(
                [
                    *create_swap(2),
                    create_instruction("LIST_APPEND", arg=1),
                ]
            )
            self.parent.push(UnknownVariable())
            all_stack_locals_metadata[1].num_stack += 1

            # current frame state
            # cells, frame_values, frame N-1 stack + leaf_resume result
            # remove frame N-1 stack from frame_values
            if num_stack > 0:
                cg.extend_output(
                    # frame_values[0] = frame_values[0][num_stack:]
                    [
                        *create_copy(2),
                        cg.create_load_const(0),
                        cg.create_binary_subscr(),
                        *create_binary_slice(num_stack, None),
                        *create_copy(3),
                        cg.create_load_const(0),
                        create_instruction("STORE_SUBSCR"),
                    ]
                )

            # current frame state
            # cells, frame_values, frame N-1 stack + leaf_resume result
            # unpack the stack (need to unpack twice since UNPACK_SEQUENCE unpacks in reverse order)
            cg.extend_output(
                [
                    create_instruction("UNPACK_SEQUENCE", arg=num_stack + 1),
                    create_instruction("BUILD_LIST", arg=num_stack + 1),
                    create_instruction("UNPACK_SEQUENCE", arg=num_stack + 1),
                ]
            )

            # call the remaining resume functions
            # current frame state
            # [frame N-1 cells, ..., frame 1 cells],
            # [
            #   frame N-1 locals,
            #   frame N-2 stack + locals,
            #   ...,
            #   frame 1 stack + locals,
            # ], *(frame N-1 stack), leaf_resume result
            self.output.add_output_instructions(
                cg.get_instructions()
                + self.parent.create_call_resume_at(
                    self.parent.next_instruction, all_stack_locals_metadata[1:]
                )
            )
        else:
            # NOTE: if WithExitFunctionVariable is reconstructed here, then the generated bytecode will be wrong.
            # However, we don't expect this to happen since WithExitFunctionVariable can only be present on the stack,
            # which must be empty in step graph breaks.
            # If we do decide to support step graph breaks with WithExitFunctionVariable in the future, we should
            # either call a skipped resume function as in the nested step graph break case, or reconstruct the
            # proper context manager object from the class (like what we used to do historically in variables/ctx_manager.py).

            # pop cells
            self.output.add_output_instructions(
                [
                    *create_swap(2),
                    create_instruction("POP_TOP"),
                ]
            )
            # load locals from frame values
            cg = PyCodegen(self.output.root_tx)
            self.output.add_output_instructions(
                [
                    cg.create_load_const(-1),
                    cg.create_binary_subscr(),
                ]
            )
            for local, idx in all_stack_locals_metadata[-1].locals_names.items():
                self.output.add_output_instructions(
                    [
                        create_dup_top(),
                        cg.create_load_const(idx),
                        cg.create_binary_subscr(),
                        cg.create_store(local),
                    ]
                )
            self.output.add_output_instructions(
                [
                    create_instruction("POP_TOP"),
                    create_jump_absolute(continue_inst),
                    *self.instructions,
                ]
            )