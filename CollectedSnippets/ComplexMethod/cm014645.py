def generate_coverage_report(
    apis: dict[str, list[tuple[str, str]]], documented: set[str]
) -> str:
    """Generate a coverage report comparing discovered APIs against RST docs."""
    lines = []
    lines.append("Undocumented C++ objects")
    lines.append("=" * 50)
    lines.append("")

    total = 0
    total_missing = 0
    section_stats = []

    for category in sorted(apis.keys()):
        symbols = apis[category]
        section_missing = []
        for symbol, kind in symbols:
            total += 1
            unqualified = symbol.rsplit("::", 1)[-1]
            if symbol not in documented and unqualified not in documented:
                section_missing.append((symbol, kind))
                total_missing += 1

        covered = len(symbols) - len(section_missing)
        section_stats.append((category, covered, len(symbols)))

        if section_missing:
            lines.append(category)
            lines.append("-" * len(category))
            for symbol, kind in section_missing:
                lines.append(f"   * {symbol}  ({kind})")
            lines.append("")

    # Summary
    total_covered = total - total_missing
    pct = (total_covered / total * 100) if total else 0

    lines.append("")
    lines.append("=" * 50)
    lines.append("Summary")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Total APIs discovered:   {total}")
    lines.append(f"Documented:              {total_covered}")
    lines.append(f"Missing:                 {total_missing}")
    lines.append(f"Coverage:                {pct:.1f}%")
    lines.append("")

    # Per-section table
    lines.append(f"{'Category':<45} {'Covered':>8} {'Total':>6} {'%':>7}")
    lines.append("-" * 70)
    for category, covered, section_total in section_stats:
        spct = (covered / section_total * 100) if section_total else 0
        lines.append(f"{category:<45} {covered:>8} {section_total:>6} {spct:>6.1f}%")
    lines.append("")

    return "\n".join(lines)