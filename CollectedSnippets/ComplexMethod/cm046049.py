def fix_two_layer_blocks(blocks, fix_type: Literal["image", "table", "chart"]):
    need_fix_blocks = get_type_blocks(blocks, fix_type)
    fixed_blocks = []
    not_include_blocks = []
    processed_indices = set()

    # 将每个block的caption_list中不连续index的元素提出来作为普通block处理
    for block in need_fix_blocks:
        caption_list = block[f"{fix_type}_caption_list"]
        body_index = block[f"{fix_type}_body"]["index"]

        # 处理caption_list (从body往前看,caption在body之前)
        if caption_list:
            # 按index降序排列,从最接近body的开始检查
            caption_list.sort(key=lambda x: x["index"], reverse=True)
            filtered_captions = [caption_list[0]]
            for i in range(1, len(caption_list)):
                prev_index = caption_list[i - 1]["index"]
                curr_index = caption_list[i]["index"]

                # 检查是否连续
                if curr_index == prev_index - 1:
                    filtered_captions.append(caption_list[i])
                else:
                    # 检查gap中是否只有body_index
                    gap_indices = set(range(curr_index + 1, prev_index))
                    if gap_indices == {body_index}:
                        # gap中只有body_index,不算真正的gap
                        filtered_captions.append(caption_list[i])
                    else:
                        # 出现真正的gap,后续所有caption都作为普通block
                        not_include_blocks.extend(caption_list[i:])
                        break
            # 恢复升序
            filtered_captions.reverse()
            block[f"{fix_type}_caption_list"] = filtered_captions

    # 构建两层结构blocks
    for block in need_fix_blocks:
        body = block[f"{fix_type}_body"]
        caption_list = block[f"{fix_type}_caption_list"]

        body["type"] = f"{fix_type}_body"
        for caption in caption_list:
            caption["type"] = f"{fix_type}_caption"
            processed_indices.add(caption["index"])

        processed_indices.add(body["index"])

        two_layer_block = {
            "type": fix_type,
            "blocks": [body],
            "index": body["index"],
        }
        two_layer_block["blocks"].extend([*caption_list])
        # 对blocks按index排序
        two_layer_block["blocks"].sort(key=lambda x: x["index"])

        fixed_blocks.append(two_layer_block)

    # 添加未处理的blocks
    for block in blocks:
        block.pop("type", None)
        if block["index"] not in processed_indices and block not in not_include_blocks:
            not_include_blocks.append(block)

    return fixed_blocks, not_include_blocks