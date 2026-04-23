def visualize_diff(
        self,
        n_context_lines: int = 2,
        change_applied: bool = True,
    ) -> str:
        """Visualize the diff of the file edit. Used in the LLM-based editing mode.

        Instead of showing the diff line by line, this function shows each hunk
        of changes as a separate entity.

        Args:
            n_context_lines: Number of context lines to show before/after changes.
            change_applied: Whether changes are applied. If false, shows as
                attempted edit.

        Returns:
            A string containing the formatted diff visualization.
        """
        # Use cached diff if available
        if self._diff_cache is not None:
            return self._diff_cache

        # Check if there are any changes
        if change_applied and self.old_content == self.new_content:
            msg = '(no changes detected. Please make sure your edits change '
            msg += 'the content of the existing file.)\n'
            self._diff_cache = msg
            return self._diff_cache

        edit_groups = self.get_edit_groups(n_context_lines=n_context_lines)

        if change_applied:
            header = f'[Existing file {self.path} is edited with '
            header += f'{len(edit_groups)} changes.]'
        else:
            header = f"[Changes are NOT applied to {self.path} - Here's how "
            header += 'the file looks like if changes are applied.]'
        result = [header]

        op_type = 'edit' if change_applied else 'ATTEMPTED edit'
        for i, cur_edit_group in enumerate(edit_groups):
            if i != 0:
                result.append('-------------------------')
            result.append(f'[begin of {op_type} {i + 1} / {len(edit_groups)}]')
            result.append(f'(content before {op_type})')
            result.extend(cur_edit_group['before_edits'])
            result.append(f'(content after {op_type})')
            result.extend(cur_edit_group['after_edits'])
            result.append(f'[end of {op_type} {i + 1} / {len(edit_groups)}]')

        # Cache the result
        self._diff_cache = '\n'.join(result)
        return self._diff_cache