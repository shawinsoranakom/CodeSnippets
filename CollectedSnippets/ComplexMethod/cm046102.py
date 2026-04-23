def absorb_image_block_members(blocks):
    image_block_bodies = [
        block for block in blocks if block["type"] == IMAGE_BLOCK_BODY
    ]
    member_candidates = [
        block
        for block in blocks
        if block["type"] in [BlockType.IMAGE_BODY, BlockType.CHART_BODY]
    ]

    assignments = {}
    for member in member_candidates:
        best_key = None
        best_parent_index = None
        for image_block in image_block_bodies:
            overlap_ratio = calculate_overlap_area_in_bbox1_area_ratio(
                member["bbox"],
                image_block["bbox"],
            )
            if overlap_ratio < 0.9:
                continue

            candidate_key = (
                -overlap_ratio,
                bbox_area(image_block["bbox"]),
                image_block["index"],
            )
            if best_key is None or candidate_key < best_key:
                best_key = candidate_key
                best_parent_index = image_block["index"]

        if best_parent_index is not None:
            assignments[member["index"]] = best_parent_index

    absorbed_member_indices = set()
    sub_images_by_index = {}
    for image_block in image_block_bodies:
        members = [
            member
            for member in member_candidates
            if assignments.get(member["index"]) == image_block["index"]
        ]
        if not members:
            continue

        members.sort(key=lambda x: x["index"])
        absorbed_member_indices.update(member["index"] for member in members)
        sub_images_by_index[image_block["index"]] = [
            {
                "type": child_visual_type(member["type"]),
                "bbox": relative_bbox(member["bbox"], image_block["bbox"]),
            }
            for member in members
        ]

    return absorbed_member_indices, sub_images_by_index