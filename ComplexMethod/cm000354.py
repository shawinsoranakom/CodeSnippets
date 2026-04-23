def generate_overview_table(blocks: list[BlockDoc], block_dir_prefix: str = "") -> str:
    """Generate the overview table markdown (blocks.md).

    Args:
        blocks: List of block documentation objects
        block_dir_prefix: Prefix for block file links (e.g., "block-integrations/")
    """
    lines = []

    # GitBook YAML frontmatter
    lines.append("---")
    lines.append("layout:")
    lines.append("  width: default")
    lines.append("  title:")
    lines.append("    visible: true")
    lines.append("  description:")
    lines.append("    visible: true")
    lines.append("  tableOfContents:")
    lines.append("    visible: false")
    lines.append("  outline:")
    lines.append("    visible: true")
    lines.append("  pagination:")
    lines.append("    visible: true")
    lines.append("  metadata:")
    lines.append("    visible: true")
    lines.append("---")
    lines.append("")

    lines.append("# AutoGPT Blocks Overview")
    lines.append("")
    lines.append(
        'AutoGPT uses a modular approach with various "blocks" to handle different tasks. These blocks are the building blocks of AutoGPT workflows, allowing users to create complex automations by combining simple, specialized components.'
    )
    lines.append("")
    lines.append('{% hint style="info" %}')
    lines.append("**Creating Your Own Blocks**")
    lines.append("")
    lines.append("Want to create your own custom blocks? Check out our guides:")
    lines.append("")
    lines.append(
        "* [Build your own Blocks](https://docs.agpt.co/platform/new_blocks/) - Step-by-step tutorial with examples"
    )
    lines.append(
        "* [Block SDK Guide](https://docs.agpt.co/platform/block-sdk-guide/) - Advanced SDK patterns with OAuth, webhooks, and provider configuration"
    )
    lines.append("{% endhint %}")
    lines.append("")
    lines.append(
        "Below is a comprehensive list of all available blocks, categorized by their primary function. Click on any block name to view its detailed documentation."
    )
    lines.append("")

    # Group blocks by category
    by_category = defaultdict[str, list[BlockDoc]](list)
    for block in blocks:
        primary_cat = block.categories[0] if block.categories else "BASIC"
        by_category[primary_cat].append(block)

    # Sort categories
    category_order = [
        "BASIC",
        "DATA",
        "TEXT",
        "AI",
        "SEARCH",
        "SOCIAL",
        "COMMUNICATION",
        "DEVELOPER_TOOLS",
        "MULTIMEDIA",
        "PRODUCTIVITY",
        "LOGIC",
        "INPUT",
        "OUTPUT",
        "AGENT",
        "CRM",
        "SAFETY",
        "ISSUE_TRACKING",
        "HARDWARE",
        "MARKETING",
    ]

    # Track emitted display names to avoid duplicate headers
    # (e.g., INPUT and OUTPUT both map to "Input/Output")
    emitted_display_names: set[str] = set()

    for category in category_order:
        if category not in by_category:
            continue

        display_name = CATEGORY_DISPLAY_NAMES.get(category, category)

        # Collect all blocks for this display name (may span multiple categories)
        if display_name in emitted_display_names:
            # Already emitted header, just add rows to existing table
            # Find the position before the last empty line and insert rows
            cat_blocks = sorted(by_category[category], key=lambda b: b.name)
            # Remove the trailing empty line, add rows, then re-add empty line
            lines.pop()
            for block in cat_blocks:
                file_mapping = get_block_file_mapping([block])
                file_path = list(file_mapping.keys())[0]
                anchor = generate_anchor(block.name)
                short_desc = (
                    block.description.split(".")[0]
                    if block.description
                    else "No description"
                )
                short_desc = short_desc.replace("\n", " ").replace("|", "\\|")
                link_path = f"{block_dir_prefix}{file_path}"
                lines.append(f"| [{block.name}]({link_path}#{anchor}) | {short_desc} |")
            lines.append("")
            continue

        emitted_display_names.add(display_name)
        cat_blocks = sorted(by_category[category], key=lambda b: b.name)

        lines.append(f"## {display_name}")
        lines.append("")
        lines.append("| Block Name | Description |")
        lines.append("|------------|-------------|")

        for block in cat_blocks:
            # Determine link path
            file_mapping = get_block_file_mapping([block])
            file_path = list(file_mapping.keys())[0]
            anchor = generate_anchor(block.name)

            # Short description (first sentence)
            short_desc = (
                block.description.split(".")[0]
                if block.description
                else "No description"
            )
            short_desc = short_desc.replace("\n", " ").replace("|", "\\|")

            link_path = f"{block_dir_prefix}{file_path}"
            lines.append(f"| [{block.name}]({link_path}#{anchor}) | {short_desc} |")

        lines.append("")

    return "\n".join(lines)