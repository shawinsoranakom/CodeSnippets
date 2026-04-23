def diff_render_lines(old: RenderLine, new: RenderLine) -> LineDiff | None:
    if old == new:
        return None

    prefix = 0
    start_x = 0
    max_prefix = min(len(old.cells), len(new.cells))
    while prefix < max_prefix and old.cells[prefix] == new.cells[prefix]:
        # Stop at any cell with non-SGR controls, since those might affect
        # cursor position and must be re-emitted.
        if old.cells[prefix].controls:
            break
        start_x += old.cells[prefix].width
        prefix += 1

    old_suffix = len(old.cells)
    new_suffix = len(new.cells)
    while old_suffix > prefix and new_suffix > prefix:
        old_cell = old.cells[old_suffix - 1]
        new_cell = new.cells[new_suffix - 1]
        if old_cell.controls or new_cell.controls or old_cell != new_cell:
            break
        old_suffix -= 1
        new_suffix -= 1

    # Extend diff range to include trailing zero-width combining characters,
    # so we never render a combining char without its base character.
    while old_suffix < len(old.cells) and old.cells[old_suffix].width == 0:
        old_suffix += 1
    while new_suffix < len(new.cells) and new.cells[new_suffix].width == 0:
        new_suffix += 1

    return LineDiff(
        start_cell=prefix,
        start_x=start_x,
        old_cells=old.cells[prefix:old_suffix],
        new_cells=new.cells[prefix:new_suffix],
        old_width=old.width,
        new_width=new.width,
    )