def create_call_resume_at(
        self,
        inst: Instruction,
        all_stack_locals_metadata: list[StackLocalsMetadata],
    ) -> list[Instruction]:
        """
        Codegen all resume function(s) from the frame stack starting at `self`, call them,
        and return the result.
        Assumes that the unsupported instruction has already been run.

        Expects the TOS to be:
            [
                frame N locals,
                frame N-1 stack + locals,
                ...,
                frame 1 stack + locals
            ], *(frame N stack (post-unsupported instruction))

        Leaves the result of calling the resume functions on the stack and returns it
        (empty stack after return).

        Args:
            - inst: the instruction of the current (deepest) frame to resume at
            - all_stack_locals_metadata: metadata returned from OutputGraph.compile_subgraph - contains
                metadata such as local names, NULL positions, stack length, etc.
        """

        self.instruction_pointer = None

        cg = PyCodegen(self.output.root_tx)

        # NOTE: We do not need to codegen frames whose resume instruction is RETURN_VALUE
        # We could also do something similar for RETURN_CONST, but a lot more code is necessary
        # since we would need to track RETURN_CONST values and inject the constant in the right places.

        # Filter out tx'es that are resuming on RETURN_*.
        txes: list[InstructionTranslatorBase] = []
        idxes: list[int] = []
        resume_insts: list[Instruction] = []
        cur_tx: InstructionTranslatorBase | None = self
        idx = 0
        while cur_tx is not None:
            if cur_tx is self:
                resume_inst = inst
            else:
                resume_inst = cur_tx.next_instruction
            if resume_inst.opname != "RETURN_VALUE":
                txes.append(cur_tx)
                idxes.append(idx)
                resume_insts.append(resume_inst)

            cur_tx = cur_tx.parent
            idx += 1

        current_num_stack = len(self.stack) - len(
            all_stack_locals_metadata[0].stack_null_idxes
        )

        # Every tx is returning - no need to call a resume function.
        if not txes:
            # Pop everything but TOS, then return the TOS.
            # Frame N's stack must have length >= 1 since it's about to RETURN_VALUE.
            # Frame N actually should have stack length == 1, because debug CPython expects
            # empty stacks after return, but there is no guarantee written down anywhere.
            assert current_num_stack >= 1
            cg.extend_output(create_swap(current_num_stack + 2))
            for _ in range(current_num_stack + 1):
                cg.append_output(create_instruction("POP_TOP"))
            cg.append_output(create_instruction("RETURN_VALUE"))

            return cg.get_instructions()

        # Let frame k be the deepest frame where the resume function is not RETURN_VALUE
        # - If k == N, then the frame N stack is prepended to the frame N locals.
        # - If k != N, then frame N's TOS is added to frame k's stack.

        # Rearrange the TOS to be compatible with create_resume and codegen_call_resume:
        #     [
        #         frame N stack + locals,
        #         ...,
        #         frame 1 stack + locals
        #     ]

        # create the stack values that should be moved
        if txes[0] is self:
            # Frame N is non-returning, pack all of frame N's stack to
            # be moved to frame N's frame values
            cg.append_output(create_instruction("BUILD_LIST", arg=current_num_stack))
            # frame N stack is not yet on the frame N's frame values
            stack_insert_idx = 0
            all_stack_locals_metadata[0].num_stack = current_num_stack
        else:
            # Frame N is returning. Let frame k be the deepest non-returning frame.
            # Add frame N's TOS to frame k's stack.
            # pop frame N stack except TOS
            cg.extend_output(create_swap(current_num_stack))
            for _ in range(current_num_stack - 1):
                cg.append_output(create_instruction("POP_TOP"))
            cg.append_output(create_instruction("BUILD_LIST", arg=1))
            # frame k stack is already on frame k's frame values
            stack_insert_idx = all_stack_locals_metadata[idxes[0]].num_stack
            all_stack_locals_metadata[idxes[0]].num_stack += 1
            txes[0].push(UnknownVariable())

        # move the predetermined stack value(s) to the deepest non-returning frame
        cg.extend_output(
            [
                *create_copy(2),
                # frame_values, return_const, frame_values
                cg.create_load_const(idxes[0]),
                cg.create_binary_subscr(),
                *create_binary_slice(stack_insert_idx, stack_insert_idx, True),
                # frame_values[idxes[0]][stack_insert_idx:stack_insert_idx] = frame N stack/[return_const/TOS]
                # frame_values left on top of stack
            ]
        )

        # filter out frame values of skipped tx'es
        filter_insts = []
        for idx in idxes:
            filter_insts.extend(
                [
                    create_dup_top(),
                    cg.create_load_const(idx),
                    cg.create_binary_subscr(),
                    *create_swap(2),
                ]
            )
        # TOS: cells, frame_values[idxes[0]], ..., frame_values[idxes[...]], frame_values
        filter_insts.extend(
            [
                create_instruction("POP_TOP"),
                create_instruction("BUILD_LIST", arg=len(idxes)),
            ]
        )
        # TOS: cells, filtered frame_values

        cg.extend_output(filter_insts)
        # filter out cells of skipped tx'es using the same instructions in filter_insts,
        # but with cells as TOS instead of frame values
        cg.extend_output(
            [
                *create_swap(2),
                *copy.deepcopy(filter_insts),
                *create_swap(2),
            ]
        )
        # TOS: filtered cells, filtered frame_values

        resume_codes: list[types.CodeType] = []
        resume_names = []
        for i, cur_tx in enumerate(txes):
            resume_code, resume_name = cur_tx.create_resume(
                i,
                resume_insts[i],
                all_stack_locals_metadata[idxes[i]],
                resume_codes,
                cg,
                cur_tx is self,
                True,
            )
            resume_codes.append(resume_code)
            resume_names.append(resume_name)

        self.codegen_call_resume(resume_codes, resume_names, cg)
        cg.append_output(create_instruction("RETURN_VALUE"))

        return cg.get_instructions()