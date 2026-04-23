def __process_blocks(blocks):
    # 对所有block预处理
    # 1.通过title和interline_equation将block分组
    # 2.bbox边界根据line信息重置

    result = []
    current_group = []

    for i in range(len(blocks)):
        current_block = blocks[i]

        # 如果当前块是 text 类型
        if current_block['type'] in [BlockType.TEXT, BlockType.INDEX, BlockType.VERTICAL_TEXT]:
            current_block['bbox_fs'] = copy.deepcopy(current_block['bbox'])
            if 'lines' in current_block and len(current_block['lines']) > 0:
                current_block['bbox_fs'] = [
                    min([line['bbox'][0] for line in current_block['lines']]),
                    min([line['bbox'][1] for line in current_block['lines']]),
                    max([line['bbox'][2] for line in current_block['lines']]),
                    max([line['bbox'][3] for line in current_block['lines']]),
                ]
            current_group.append(current_block)

        # 检查下一个块是否存在
        if i + 1 < len(blocks):
            next_block = blocks[i + 1]
            # 如果下一个块不是 text 类型且是 title 或 interline_equation 类型
            if next_block['type'] in [
                BlockType.ABSTRACT,
                BlockType.INTERLINE_EQUATION,
                BlockType.DOC_TITLE,
                BlockType.PARAGRAPH_TITLE,
            ]:
                result.append(current_group)
                current_group = []

    # 处理最后一个 group
    if current_group:
        result.append(current_group)

    return result