def classify_caption_blocks(page_blocks: list) -> list:
    """
    对page_blocks中的caption块进行分类，将其分类为image_caption、table_caption或chart_caption。

    规则：
    1. 只有与type为table、image或chart相邻的caption可以作为caption
    2. caption块与table、image或chart中相隔的块全部是caption的情况视为该caption块与母块相邻
    3. caption的类型与他前置位相邻的母块type一致，如果没有前置位母块则检查是否有后置位母块
    4. 没有相邻母块的caption需要变更type为text
    5. 当一个block的type是table、image或chart时，其后续的第一个text块如果以特定前缀开头，则将其设置为相应的caption类型
       - table后的text块以["表", "table"]开头（不区分大小写）-> table_caption
       - image后的text块以["图", "fig"]开头（不区分大小写）-> image_caption
       - chart后的text块以["图", "fig", "chart"]开头（不区分大小写）-> chart_caption
    """
    if not page_blocks:
        return page_blocks

    available_types = ["table", "image", "chart"]

    # 定义caption前缀匹配规则
    table_caption_prefixes = ["表", "table"]
    image_caption_prefixes = ["图", "fig"]
    chart_caption_prefixes = ["图", "fig", "chart"]

    # 第一步：处理table/image/chart后续的text块，将符合条件的text块标记为caption
    preprocessed_blocks = []
    n = len(page_blocks)

    for i, block in enumerate(page_blocks):
        block_type = block.get("type")

        # 检查是否是table或image块
        if block_type in available_types:
            preprocessed_blocks.append(block)

            # 查找后续的第一个text块
            if i + 1 < n:
                next_block = page_blocks[i + 1]
                next_block_type = next_block.get("type")

                if next_block_type == "text":
                    content = next_block.get("content", "").strip().lower()

                    # 根据当前块类型检查是否匹配caption前缀
                    if block_type == "table":
                        if any(content.startswith(prefix.lower()) for prefix in table_caption_prefixes):
                            # 将text块标记为caption，后续会被处理为table_caption
                            next_block = next_block.copy()
                            next_block["type"] = "caption"
                            page_blocks[i + 1] = next_block
                    elif block_type == "image":
                        if any(content.startswith(prefix.lower()) for prefix in image_caption_prefixes):
                            # 将text块标记为caption，后续会被处理为image_caption
                            next_block = next_block.copy()
                            next_block["type"] = "caption"
                            page_blocks[i + 1] = next_block
                    elif block_type == "chart":
                        if any(content.startswith(prefix.lower()) for prefix in chart_caption_prefixes):
                            # 将text块标记为caption，后续会被处理为chart_caption
                            next_block = next_block.copy()
                            next_block["type"] = "caption"
                            page_blocks[i + 1] = next_block
        else:
            preprocessed_blocks.append(block)

    # 第二步：处理caption块的分类
    result_blocks = []

    for i, block in enumerate(page_blocks):
        if block.get("type") != "caption":
            result_blocks.append(block)
            continue

        # 查找前置位相邻的母块（table、image或chart）
        # 向前查找，跳过连续的caption块
        prev_parent_type = None
        j = i - 1
        while j >= 0:
            prev_block_type = page_blocks[j].get("type")
            if prev_block_type in available_types:
                prev_parent_type = prev_block_type
                break
            elif prev_block_type == "caption":
                # 继续向前查找
                j -= 1
            else:
                # 遇到非caption且非table/image/chart的块，停止查找
                break

        # 查找后置位相邻的母块（table、image或chart）
        # 向后查找，跳过连续的caption块
        next_parent_type = None
        k = i + 1
        while k < n:
            next_block_type = page_blocks[k].get("type")
            if next_block_type in available_types:
                next_parent_type = next_block_type
                break
            elif next_block_type == "caption":
                # 继续向后查找
                k += 1
            else:
                # 遇到非caption且非table/image/chart的块，停止查找
                break

        # 根据规则确定caption类型
        new_block = block.copy()
        if prev_parent_type:
            # 优先使用前置位母块的类型
            new_block["type"] = f"{prev_parent_type}_caption"
        elif next_parent_type:
            # 没有前置位母块，使用后置位母块的类型
            new_block["type"] = f"{next_parent_type}_caption"
        else:
            # 没有相邻母块，变更为text
            new_block["type"] = "text"

        result_blocks.append(new_block)

    return result_blocks