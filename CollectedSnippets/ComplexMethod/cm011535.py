def _print_discrepancy_section(
    title: str, discrepancies: list[Discrepancy], show_repro: int = 0
) -> None:
    """Print grouped discrepancies for a section (incorrect or missing)."""
    if not discrepancies:
        return
    print(f"\n{title}")
    by_op: dict[str, dict[ComboKey, list[Discrepancy]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for d in discrepancies:
        op_str = str(d.aten_op)
        key = (d.input_placements, d.output_placements)
        by_op[op_str][key].append(d)

    for op_str in sorted(by_op.keys()):
        print(f"\n  [{op_str}]")
        for (inp, out), discs in sorted(by_op[op_str].items(), key=str):
            inp_str = ", ".join(inp)
            out_str = out[0] if len(out) == 1 else "(" + ", ".join(out) + ")"
            print(f"    {inp_str} -> {out_str}")
            if show_repro:
                limit = len(discs) if show_repro < 0 else show_repro
                for d in discs[:limit]:
                    if d.sample is not None:
                        print(
                            f"      Repro: {_format_sample_repro(d.sample, d.aten_op)}"
                        )
                if len(discs) > limit:
                    print(f"      ... and {len(discs) - limit} more")