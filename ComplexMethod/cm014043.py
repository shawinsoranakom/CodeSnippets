def find_orig_offset_transform(
                instructions: list[Instruction], code_options: dict[str, Any]
            ) -> None:
                nonlocal orig_offset
                (target,) = (i for i in instructions if i.offset == cur_offset)
                # match the functions starting at the last instruction as we have added a prefix
                new_target_tuple = tuple(
                    i2
                    for i1, i2 in zip(
                        reversed(instructions), reversed(meta.instructions)
                    )
                    if i1 is target
                )

                if not new_target_tuple:
                    # Instruction with cur_offset in instructions was not found
                    # in the original code - orig_offset left as -1.
                    # Caller expected to handle this case.
                    return

                assert len(new_target_tuple) == 1
                new_target = new_target_tuple[0]

                assert target.opcode == new_target.opcode
                assert new_target.offset is not None
                orig_offset = new_target.offset