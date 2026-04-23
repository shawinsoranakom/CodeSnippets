def remap_block_offsets(
                    instructions: list[Instruction], code_options: dict[str, Any]
                ) -> None:
                    # NOTE: each prefix block generates exactly one PUSH_EXC_INFO,
                    # so we can tell which block a prefix PUSH_EXC_INFO belongs to,
                    # by counting. Then we can use meta.prefix_block_target_offset_remap
                    # to determine where in the original code the PUSH_EXC_INFO offset
                    # replaced.
                    prefix_blocks: list[Instruction] = []
                    for inst in instructions:
                        # NOTE meta.prefix_block_target_offset_remap is based off of how we codegen'd
                        # context managers at the prefix/prologue of the resume function. It is the same for
                        # every graph break in the same resume function, so we do not need to recompute
                        # for each graph break (unlike for meta.block_target_offset_remap)
                        if len(prefix_blocks) == len(
                            meta.prefix_block_target_offset_remap
                        ):
                            break
                        if inst.opname == "PUSH_EXC_INFO":
                            prefix_blocks.append(inst)

                    # remap block target offsets for blocks generated in the resume prefix
                    for inst, o in zip(
                        prefix_blocks, meta.prefix_block_target_offset_remap
                    ):
                        block_target_offset_remap[cast(int, inst.offset)] = o

                    # current bytecode targets are after the prefix PUSH_EXC_INFO's
                    cur_start_offset = (
                        cast(int, prefix_blocks[-1].offset) if prefix_blocks else -1
                    )
                    # get the remaining block target offsets of the current bytecode
                    cur_inst_offsets = sorted(
                        n for n in setup_fn_target_offsets if n > cur_start_offset
                    )
                    targets = _filter_iter(
                        instructions, cur_inst_offsets, lambda inst, o: inst.offset == o
                    )
                    # The original code and resume code should have matching suffixes.
                    # Match the post-prefix block target offsets of the current resume code
                    # and the original code.
                    orig_targets = reversed(
                        _filter_iter(
                            zip(reversed(instructions), reversed(meta.instructions)),
                            reversed(targets),
                            lambda v1, v2: v1[0] is v2,
                        )
                    )
                    for orig, cur in zip(orig_targets, targets):
                        block_target_offset_remap[cur.offset] = orig[1].offset