def _format_module_tree(
    module: nn.Module,
    name: str = "",
    indent: int = 0,
) -> list[str]:
    """Format a module tree with indentation, grouping identical layers.

    Produces output like:
        (layers): ModuleList(
          (0-27, 29-47): 47 x LlamaDecoderLayer(
            ...
          )
          (28, 48): 2 x DifferentDecoderLayer(
            ...
          )
        )
    """
    lines = []
    prefix = "  " * indent
    children = list(module.named_children())

    # Leaf node - just output the module info
    if not children:
        info = _get_module_info(module)
        lines.append(f"{prefix}({name}): {info}" if name else f"{prefix}{info}")
        return lines

    # Non-leaf node - output opening line and recurse into children
    info = _get_module_info(module)
    lines.append(f"{prefix}({name}): {info}(" if name else f"{prefix}{info}(")

    # Separate numbered children (e.g., "0", "1") from named ones (e.g., "norm")
    numbered: list[tuple[int, nn.Module]] = []
    non_numbered: list[tuple[str, nn.Module]] = []
    for child_name, child_module in children:
        try:
            numbered.append((int(child_name), child_module))
        except ValueError:
            non_numbered.append((child_name, child_module))

    # Group numbered children by structure signature to collapse identical layers
    # e.g., layers 0-27 and 29-47 with same structure become "(0-27, 29-47): 47 x"
    if numbered:
        sig_to_group: dict[str, list[tuple[int, nn.Module]]] = {}
        for idx, child_module in numbered:
            sig = _get_child_signature(child_module)
            sig_to_group.setdefault(sig, []).append((idx, child_module))

        # Output groups sorted by first index
        for group in sorted(sig_to_group.values(), key=lambda g: g[0][0]):
            indices = [idx for idx, _ in group]
            representative = group[0][1]
            child_lines = _format_module_tree(representative, "", indent + 1)
            first_line = child_lines[0].lstrip()
            child_prefix = "  " * (indent + 1)

            if len(indices) > 1:
                range_str = _format_index_ranges(indices)
                child_lines[0] = (
                    f"{child_prefix}({range_str}): {len(indices)} x {first_line}"
                )
            else:
                child_lines[0] = f"{child_prefix}({indices[0]}): {first_line}"
            lines.extend(child_lines)

    # Output non-numbered children (e.g., "embed_tokens", "norm")
    for child_name, child_module in non_numbered:
        lines.extend(_format_module_tree(child_module, child_name, indent + 1))

    lines.append(f"{prefix})")
    return lines