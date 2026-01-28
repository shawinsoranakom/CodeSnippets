def get_blocks(
    *,
    category: str | None = None,
    type: BlockType | None = None,
    provider: ProviderName | None = None,
    page: int = 1,
    page_size: int = 50,
) -> BlockResponse:
    """
    Get blocks based on either category, type or provider.
    Providing nothing fetches all block types.
    """
    # Only one of category, type, or provider can be specified
    if (category and type) or (category and provider) or (type and provider):
        raise ValueError("Only one of category, type, or provider can be specified")

    blocks: list[AnyBlockSchema] = []
    skip = (page - 1) * page_size
    take = page_size
    total = 0

    for block_type in load_all_blocks().values():
        block: AnyBlockSchema = block_type()
        # Skip disabled blocks
        if block.disabled:
            continue
        # Skip blocks that don't match the category
        if category and category not in {c.name.lower() for c in block.categories}:
            continue
        # Skip blocks that don't match the type
        if (
            (type == "input" and block.block_type.value != "Input")
            or (type == "output" and block.block_type.value != "Output")
            or (type == "action" and block.block_type.value in ("Input", "Output"))
        ):
            continue
        # Skip blocks that don't match the provider
        if provider:
            credentials_info = block.input_schema.get_credentials_fields_info().values()
            if not any(provider in info.provider for info in credentials_info):
                continue

        total += 1
        if skip > 0:
            skip -= 1
            continue
        if take > 0:
            take -= 1
            blocks.append(block)

    return BlockResponse(
        blocks=[b.get_info() for b in blocks],
        pagination=Pagination(
            total_items=total,
            total_pages=(total + page_size - 1) // page_size,
            current_page=page,
            page_size=page_size,
        ),
    )
