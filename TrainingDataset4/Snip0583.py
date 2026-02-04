def generate_block_markdown(
    block: BlockDoc,
    manual_content: dict[str, str] | None = None,
) -> str:
    """Generate markdown documentation for a single block."""
    manual_content = manual_content or {}
    lines = []

    # All blocks use ## heading, sections use ### (consistent siblings)
    lines.append(f"## {block.name}")
    lines.append("")

    # What it is (full description)
    lines.append("### What it is")
    lines.append(block.description or "No description available.")
    lines.append("")

    # How it works (manual section)
    lines.append("### How it works")
    how_it_works = manual_content.get(
        "how_it_works", "_Add technical explanation here._"
    )
    lines.append("<!-- MANUAL: how_it_works -->")
    lines.append(how_it_works)
    lines.append("<!-- END MANUAL -->")
    lines.append("")

    # Inputs table (auto-generated)
    visible_inputs = [f for f in block.inputs if not f.hidden]
    if visible_inputs:
        lines.append("### Inputs")
        lines.append("")
        lines.append("| Input | Description | Type | Required |")
        lines.append("|-------|-------------|------|----------|")
        for inp in visible_inputs:
            required = "Yes" if inp.required else "No"
            desc = inp.description or "-"
            type_str = inp.type_str or "-"
            # Normalize newlines and escape pipes for valid table syntax
            desc = desc.replace("\n", " ").replace("|", "\\|")
            type_str = type_str.replace("|", "\\|")
            lines.append(f"| {inp.name} | {desc} | {type_str} | {required} |")
        lines.append("")

    # Outputs table (auto-generated)
    visible_outputs = [f for f in block.outputs if not f.hidden]
    if visible_outputs:
        lines.append("### Outputs")
        lines.append("")
        lines.append("| Output | Description | Type |")
        lines.append("|--------|-------------|------|")
        for out in visible_outputs:
            desc = out.description or "-"
            type_str = out.type_str or "-"
            # Normalize newlines and escape pipes for valid table syntax
            desc = desc.replace("\n", " ").replace("|", "\\|")
            type_str = type_str.replace("|", "\\|")
            lines.append(f"| {out.name} | {desc} | {type_str} |")
        lines.append("")

    # Possible use case (manual section)
    lines.append("### Possible use case")
    use_case = manual_content.get("use_case", "_Add practical use case examples here._")
    lines.append("<!-- MANUAL: use_case -->")
    lines.append(use_case)
    lines.append("<!-- END MANUAL -->")
    lines.append("")

    # Optional per-block extras (only include if has content)
    extras = manual_content.get("extras", "")
    if extras:
        lines.append("<!-- MANUAL: extras -->")
        lines.append(extras)
        lines.append("<!-- END MANUAL -->")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)
