def regroup_visual_blocks(blocks):
    ordered_blocks = sorted(blocks, key=lambda x: x["index"])
    absorbed_member_indices, sub_images_by_index = absorb_image_block_members(ordered_blocks)
    effective_blocks = [
        block for block in ordered_blocks if block["index"] not in absorbed_member_indices
    ]
    position_by_index = {
        block["index"]: pos for pos, block in enumerate(effective_blocks)
    }
    main_blocks = [
        block for block in effective_blocks if block["type"] in VISUAL_MAIN_TYPES
    ]
    child_blocks = [
        block for block in effective_blocks if block["type"] in GENERIC_CHILD_TYPES
    ]

    grouped_children = {
        block["index"]: {"captions": [], "footnotes": []} for block in main_blocks
    }
    unmatched_child_blocks = []

    for main_block in main_blocks:
        if main_block["index"] in sub_images_by_index:
            main_block["sub_images"] = sub_images_by_index[main_block["index"]]

    for child_block in child_blocks:
        parent_block = find_best_visual_parent(
            child_block,
            main_blocks,
            effective_blocks,
            position_by_index,
        )
        if parent_block is None:
            unmatched_child_blocks.append(child_block)
            continue

        child_kind = child_kind_from_type(child_block["type"])
        grouped_children[parent_block["index"]][f"{child_kind}s"].append(child_block)

    grouped_blocks = {
        BlockType.IMAGE: [],
        BlockType.TABLE: [],
        BlockType.CHART: [],
        BlockType.CODE: [],
    }

    for main_block in main_blocks:
        visual_type = VISUAL_MAIN_TYPES[main_block["type"]]
        mapping = VISUAL_TYPE_MAPPING[visual_type]
        body_block = dict(main_block)
        body_block["type"] = mapping["body"]
        body_block.pop("sub_images", None)
        body_block.pop("sub_type", None)

        captions = []
        for caption in sorted(
            grouped_children[main_block["index"]]["captions"],
            key=lambda x: x["index"],
        ):
            child_block = dict(caption)
            child_block["type"] = mapping["caption"]
            captions.append(child_block)

        footnotes = []
        for footnote in sorted(
            grouped_children[main_block["index"]]["footnotes"],
            key=lambda x: x["index"],
        ):
            child_block = dict(footnote)
            child_block["type"] = mapping["footnote"]
            footnotes.append(child_block)

        two_layer_block = {
            "type": visual_type,
            "bbox": body_block["bbox"],
            "blocks": [body_block, *captions, *footnotes],
            "index": body_block["index"],
        }
        if visual_type in [BlockType.IMAGE, BlockType.CHART] and main_block.get("sub_type"):
            two_layer_block["sub_type"] = main_block["sub_type"]
        if visual_type == BlockType.IMAGE and main_block.get("sub_images"):
            two_layer_block["sub_images"] = main_block["sub_images"]
        if visual_type == BlockType.TABLE and main_block.get("cell_merge"):
            two_layer_block["cell_merge"] = main_block["cell_merge"]
        two_layer_block["blocks"].sort(key=lambda x: x["index"])

        grouped_blocks[visual_type].append(two_layer_block)

    for blocks_of_type in grouped_blocks.values():
        blocks_of_type.sort(key=lambda x: x["index"])

    return grouped_blocks, unmatched_child_blocks