def get_verbose_code_parts(
    code_parts: str | list[str],
    guard: Guard | None,
    recompile_hint: str | None = None,
) -> list[str]:
    if not isinstance(code_parts, list):
        code_parts = [code_parts]

    verbose_code_parts = [
        get_verbose_code_part(code_part, guard) for code_part in code_parts
    ]

    # For CellContentsSource (or any source with a CellContentsSource ancestor),
    # add a hint explaining which closure variable is being checked.
    # This helps users understand which closure variable caused the guard failure.
    if guard is not None:
        closure_hint = _get_closure_var_hint(guard.originating_source)
        if closure_hint:
            recompile_hint = (
                f"{closure_hint}, {recompile_hint}" if recompile_hint else closure_hint
            )

    if recompile_hint:
        verbose_code_parts = [
            f"{part} (HINT: {recompile_hint})" for part in verbose_code_parts
        ]

    return verbose_code_parts