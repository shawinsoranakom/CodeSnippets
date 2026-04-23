def __plan_changed_line(  # keep in sync with UnixConsole.__plan_changed_line
        self,
        y: int,
        oldline: RenderLine,
        newline: RenderLine,
        px_coord: int,
    ) -> LineUpdate | None:
        diff = diff_render_lines(oldline, newline)
        if diff is None:
            return None

        start_cell = diff.start_cell
        start_x = diff.start_x
        if (
            len(diff.old_cells) == 1
            and len(diff.new_cells) == 1
            and diff.old_cells[0].width == diff.new_cells[0].width
        ):
            changed_cell = diff.new_cells[0]
            # Ctrl-Z (SUB) can reach here via RenderLine.from_rendered_text()
            # for prompt/message lines, which bypasses iter_display_chars().
            # On Windows, raw \x1a causes console cursor anomalies, so we
            # force a cursor resync when it appears.
            return LineUpdate(
                kind="replace_char",
                y=y,
                start_cell=start_cell,
                start_x=start_x,
                cells=diff.new_cells,
                char_width=changed_cell.width,
                reset_to_margin=(
                    requires_cursor_resync(diff.new_cells)
                    or "\x1a" in changed_cell.text
                ),
            )

        if diff.old_changed_width == diff.new_changed_width:
            return LineUpdate(
                kind="replace_span",
                y=y,
                start_cell=start_cell,
                start_x=start_x,
                cells=diff.new_cells,
                char_width=diff.new_changed_width,
                reset_to_margin=(
                    requires_cursor_resync(diff.new_cells)
                    or any("\x1a" in cell.text for cell in diff.new_cells)
                ),
            )

        suffix_cells = newline.cells[start_cell:]
        return LineUpdate(
            kind="rewrite_suffix",
            y=y,
            start_cell=start_cell,
            start_x=start_x,
            cells=suffix_cells,
            char_width=sum(cell.width for cell in suffix_cells),
            clear_eol=oldline.width > newline.width,
            reset_to_margin=(
                requires_cursor_resync(suffix_cells)
                or any("\x1a" in cell.text for cell in suffix_cells)
            ),
        )