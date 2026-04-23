def __plan_changed_line(
        self,
        y: int,
        oldline: RenderLine,
        newline: RenderLine,
        px_coord: int,
    ) -> LineUpdate | None:
        # NOTE: The shared replace_char / replace_span / rewrite_suffix logic
        # is duplicated in WindowsConsole.__plan_changed_line. Keep changes to
        # these common cases synchronised between the two files. Yes, this is
        # duplicated on purpose; the two backends agree just enough to make a
        # shared helper a trap. Unix-only cases (insert_char, delete_then_insert)
        # rely on terminal capabilities (ich1/dch1) that are unavailable on
        # Windows.
        diff = diff_render_lines(oldline, newline)
        if diff is None:
            return None

        start_cell = diff.start_cell
        start_x = diff.start_x

        if (
            self.ich1
            and not diff.old_cells
            and (visible_new_cells := tuple(
                cell for cell in diff.new_cells if cell.width
            ))
            and len(visible_new_cells) == 1
            and all(cell.width == 0 for cell in diff.new_cells[1:])
            and oldline.cells[start_cell:] == newline.cells[start_cell + 1 :]
        ):
            px_cell = self.__cell_index_from_x(oldline, px_coord)
            if (
                y == self.posxy[1]
                and start_x > self.posxy[0]
                and oldline.cells[px_cell:start_cell]
                == newline.cells[px_cell + 1 : start_cell + 1]
            ):
                start_cell = px_cell
                start_x = px_coord
            planned_cells = diff.new_cells
            changed_cell = visible_new_cells[0]
            return LineUpdate(
                kind="insert_char",
                y=y,
                start_cell=start_cell,
                start_x=start_x,
                cells=planned_cells,
                char_width=changed_cell.width,
                reset_to_margin=requires_cursor_resync(planned_cells),
            )

        if (
            len(diff.old_cells) == 1
            and len(diff.new_cells) == 1
            and diff.old_cells[0].width == diff.new_cells[0].width
        ):
            planned_cells = diff.new_cells
            changed_cell = planned_cells[0]
            return LineUpdate(
                kind="replace_char",
                y=y,
                start_cell=start_cell,
                start_x=start_x,
                cells=planned_cells,
                char_width=changed_cell.width,
                reset_to_margin=requires_cursor_resync(planned_cells),
            )

        if diff.old_changed_width == diff.new_changed_width:
            planned_cells = diff.new_cells
            return LineUpdate(
                kind="replace_span",
                y=y,
                start_cell=start_cell,
                start_x=start_x,
                cells=planned_cells,
                char_width=diff.new_changed_width,
                reset_to_margin=requires_cursor_resync(planned_cells),
            )

        if (
            self.dch1
            and self.ich1
            and newline.width == self.width
            and start_x < newline.width - 2
            and newline.cells[start_cell + 1 : -1] == oldline.cells[start_cell:-2]
        ):
            planned_cells = (newline.cells[start_cell],)
            changed_cell = planned_cells[0]
            return LineUpdate(
                kind="delete_then_insert",
                y=y,
                start_cell=start_cell,
                start_x=start_x,
                cells=planned_cells,
                char_width=changed_cell.width,
                reset_to_margin=requires_cursor_resync(planned_cells),
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
            reset_to_margin=requires_cursor_resync(suffix_cells),
        )