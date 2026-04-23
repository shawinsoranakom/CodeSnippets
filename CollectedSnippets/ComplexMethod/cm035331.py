def get_edit_groups(self, n_context_lines: int = 2) -> list[dict[str, list[str]]]:
        """Get the edit groups showing changes between old and new content.

        Args:
            n_context_lines: Number of context lines to show around each change.

        Returns:
            A list of edit groups, where each group contains before/after edits.
        """
        if self.old_content is None or self.new_content is None:
            return []
        old_lines = self.old_content.split('\n')
        new_lines = self.new_content.split('\n')
        # Borrowed from difflib.unified_diff to directly parse into structured format
        edit_groups: list[dict] = []
        for group in SequenceMatcher(None, old_lines, new_lines).get_grouped_opcodes(
            n_context_lines
        ):
            # Take the max line number in the group
            _indent_pad_size = len(str(group[-1][3])) + 1  # +1 for "*" prefix
            cur_group: dict[str, list[str]] = {
                'before_edits': [],
                'after_edits': [],
            }
            for tag, i1, i2, j1, j2 in group:
                if tag == 'equal':
                    for idx, line in enumerate(old_lines[i1:i2]):
                        line_num = i1 + idx + 1
                        cur_group['before_edits'].append(
                            f'{line_num:>{_indent_pad_size}}|{line}'
                        )
                    for idx, line in enumerate(new_lines[j1:j2]):
                        line_num = j1 + idx + 1
                        cur_group['after_edits'].append(
                            f'{line_num:>{_indent_pad_size}}|{line}'
                        )
                    continue
                if tag in {'replace', 'delete'}:
                    for idx, line in enumerate(old_lines[i1:i2]):
                        line_num = i1 + idx + 1
                        cur_group['before_edits'].append(
                            f'-{line_num:>{_indent_pad_size - 1}}|{line}'
                        )
                if tag in {'replace', 'insert'}:
                    for idx, line in enumerate(new_lines[j1:j2]):
                        line_num = j1 + idx + 1
                        cur_group['after_edits'].append(
                            f'+{line_num:>{_indent_pad_size - 1}}|{line}'
                        )
            edit_groups.append(cur_group)
        return edit_groups