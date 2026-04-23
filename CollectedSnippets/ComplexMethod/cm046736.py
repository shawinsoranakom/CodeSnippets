def _apply_user_mapping(dataset, mapping: dict, batch_size: int = 1000):
    """
    Apply user-provided column mapping to convert dataset to conversations format.

    Accepts chatml (user/assistant/system), sharegpt (human/gpt/system), and
    alpaca (instruction/input/output) role names — all normalised to chatml output.

    If the mapping contains ``__``-prefixed metadata keys (from the conversion
    advisor), routes to template-based conversion instead of simple role mapping.

    Returns:
        Dataset with single 'conversations' column
    """
    # Split metadata from column roles
    meta = {k: v for k, v in mapping.items() if k.startswith("__")}
    column_roles = {k: v for k, v in mapping.items() if not k.startswith("__")}

    if meta:
        return _apply_template_mapping(dataset, column_roles, meta, batch_size)

    # ── Simple mode (original logic) ──
    # Pre-compute: group columns by canonical chatml role
    role_groups: dict[str, list[str]] = {r: [] for r in _CHATML_ROLE_ORDER}
    for col_name, role in column_roles.items():
        canonical = _TO_CHATML.get(role)
        if canonical:
            role_groups[canonical].append(col_name)

    def _convert(examples):
        num = len(next(iter(examples.values())))
        conversations = []
        for i in range(num):
            convo = []
            for chatml_role in _CHATML_ROLE_ORDER:
                for col in role_groups[chatml_role]:
                    if col in examples:
                        content = examples[col][i]
                        convo.append(
                            {
                                "role": chatml_role,
                                "content": str(content) if content else "",
                            }
                        )
            conversations.append(convo)
        return {"conversations": conversations}

    return dataset.map(
        _convert,
        batched = True,
        batch_size = batch_size,
        remove_columns = dataset.column_names,
    )