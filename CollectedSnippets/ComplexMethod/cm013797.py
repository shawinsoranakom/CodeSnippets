def _check_backward_seq_id_uniqueness(events: list[dict]) -> list[Violation]:
    """Per Sequence number, at most one distinct backward op name."""
    seq_to_ops: dict[int, list[str]] = defaultdict(list)
    for ev in events:
        if ev.get("ph") != "X":
            continue
        name = ev.get("name", "")
        if "autograd::engine::evaluate_function:" not in name:
            continue
        args = ev.get("args", {})
        seq = args.get("Sequence number") or args.get("seq_num")
        if seq is None:
            continue
        seq = int(seq)
        op = name.split(":", 1)[-1].strip() if ":" in name else name
        if op not in seq_to_ops[seq]:
            seq_to_ops[seq].append(op)

    violations = []
    for seq, ops in seq_to_ops.items():
        if len(ops) > 1:
            violations.append(
                Violation(
                    rule_name="_check_backward_seq_id_uniqueness",
                    message=(
                        f"Sequence number {seq} shared by {len(ops)} backward "
                        f"ops: {ops}"
                    ),
                )
            )
    return violations