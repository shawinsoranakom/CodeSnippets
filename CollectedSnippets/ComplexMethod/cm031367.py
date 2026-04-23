def render_cells(
    cells: Sequence[RenderCell],
    visual_style: str | None = None,
) -> str:
    """Render a sequence of cells into a terminal string with SGR escapes.

    Tracks the active SGR state to emit resets only when the style
    actually changes, minimizing output bytes.

    If *visual_style* is given (used by redraw visualization), it is appended
    to every cell's style.
    """
    rendered: list[str] = []
    active_escape = ""
    for cell in cells:
        if cell.controls:
            rendered.extend(cell.controls)
        if not cell.text:
            continue

        target_escape = _style_escape(cell.style)
        if visual_style is not None:
            target_escape += visual_style
        if target_escape != active_escape:
            if active_escape:
                rendered.append("\x1b[0m")
            if target_escape:
                rendered.append(target_escape)
            active_escape = target_escape
        rendered.append(cell.text)

    if active_escape:
        rendered.append("\x1b[0m")
    return "".join(rendered)