def validate_lines(self, lines_dict: dict, problems: list) -> bool:
        """Validates the lines of the hunk against the original file and returns a boolean value accordingly. If the lines do not match, it appends a problem message to the problems list."""
        hunk_ind = 0
        file_ind = self.start_line_pre_edit
        # make an orig hunk lines for logging
        # orig_hunk_lines = deepcopy(self.lines)
        while hunk_ind < len(self.lines) and file_ind <= max(lines_dict):
            if self.lines[hunk_ind][0] == ADD:
                # this cannot be validated, jump one index
                hunk_ind += 1
            elif not is_similar(self.lines[hunk_ind][1], lines_dict[file_ind]):
                # before we go any further, we should relabel the comment from LLM
                if self.lines[hunk_ind][1].count("#") > 0:
                    self.relabel_line(hunk_ind, ADD)
                    continue

                # make a forward block from the code for comparisons
                forward_code = "\n".join(
                    [
                        lines_dict[ind]
                        for ind in range(
                            file_ind,
                            min(
                                file_ind + self.forward_block_len,
                                max(lines_dict.keys()),
                            ),
                        )
                    ]
                )
                # make the original forward block for quantitative comparison
                forward_block = self.make_forward_block(
                    hunk_ind, self.forward_block_len
                )
                orig_count_ratio = count_ratio(forward_block, forward_code)
                # Here we have 2 cases
                # 1) some lines were simply skipped in the diff and we should add them to the diff
                # If this is the case, adding the line to the diff, should give an improved forward diff
                forward_block_missing_line = self.make_forward_block(
                    hunk_ind, self.forward_block_len - 1
                )
                # insert the missing line in front of the block
                forward_block_missing_line = "\n".join(
                    [lines_dict[file_ind], forward_block_missing_line]
                )
                missing_line_count_ratio = count_ratio(
                    forward_block_missing_line, forward_code
                )
                # 2) Additional lines, not belonging to the code were added to the diff
                forward_block_false_line = self.make_forward_block(
                    hunk_ind + 1, self.forward_block_len
                )
                false_line_count_ratio = count_ratio(
                    forward_block_false_line, forward_code
                )
                if (
                    orig_count_ratio >= missing_line_count_ratio
                    and orig_count_ratio >= false_line_count_ratio
                ):
                    problems.append(
                        f"In Hunk:{self.hunk_to_string()}, there was at least one mismatch."
                    )
                    return False

                elif missing_line_count_ratio > false_line_count_ratio:
                    self.add_retained_line(lines_dict[file_ind], hunk_ind)
                    hunk_ind += 1
                    file_ind += 1
                    # NOTE: IF THE LLM SKIPS SOME LINES AND HAS ADDs ADJACENT TO THE SKIPPED BLOCK,
                    # WE CANNOT KNOW WHETHER THE ADDs SHOULD BE BEFORE OR AFTER THE BLOCK. WE OPT FOR PUTTING IT BEFORE.
                    # IF IT MATTERED, WE ASSUME THE LLM WOULD NOT SKIP THE BLOCK
                else:
                    self.pop_line(self.lines[hunk_ind], hunk_ind)

            else:
                hunk_ind += 1
                file_ind += 1
        # if we have not validated all lines, we have a problem
        if hunk_ind < len(self.lines) - 1:
            remaining_lines = "\n".join(
                f"{line_type}: {line_content}"
                for line_type, line_content in self.lines[file_ind + 1 :]
            )
            problems.append(
                f"In {self.hunk_to_string()}:Hunk validation stopped before the lines {remaining_lines} were validated. The diff is incorrect"
            )
            return False
        return True