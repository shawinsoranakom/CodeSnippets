def __merge_2_text_blocks(block1, block2):
    if len(block1['lines']) > 0 and len(block2['lines']) > 0:
        first_line = block1['lines'][0]
        line_height = first_line['bbox'][3] - first_line['bbox'][1]
        block1_weight = block1['bbox'][2] - block1['bbox'][0]
        block2_weight = block2['bbox'][2] - block2['bbox'][0]
        min_block_weight = min(block1_weight, block2_weight)
        if abs(block1['bbox_fs'][0] - first_line['bbox'][0]) < line_height / 2:
            last_line = block2['lines'][-1]
            if len(last_line['spans']) > 0:
                last_span = last_line['spans'][-1]
                line_height = last_line['bbox'][3] - last_line['bbox'][1]
                if len(first_line['spans']) > 0:
                    first_span = first_line['spans'][0]
                    if len(first_span['content']) > 0:
                        span_start_with_num = first_span['content'][0].isdigit()
                        span_start_with_big_char = first_span['content'][0].isupper()
                        if (
                            # 上一个block的最后一个line的右边界和block的右边界差距不超过line_height
                            abs(block2['bbox_fs'][2] - last_line['bbox'][2]) < line_height
                            # 上一个block的最后一个span不是以特定符号结尾
                            and not last_span['content'].endswith(LINE_STOP_FLAG)
                            # 两个block宽度差距超过2倍也不合并
                            and abs(block1_weight - block2_weight) < min_block_weight
                            # 下一个block的第一个字符是数字
                            and not span_start_with_num
                            # 下一个block的第一个字符是大写字母
                            and not span_start_with_big_char
                            # 下一个块的y0要比上一个块的y1小
                            and block1['bbox'][1] < block2['bbox'][3]
                            # 两个块任意一个块需要大于1行
                            and (len(block1['lines']) > 1 or len(block2['lines']) > 1)
                        ):
                            if block1['page_num'] != block2['page_num']:
                                for line in block1['lines']:
                                    for span in line['spans']:
                                        span[SplitFlag.CROSS_PAGE] = True
                            block2['lines'].extend(block1['lines'])
                            block1['lines'] = []
                            block1[SplitFlag.LINES_DELETED] = True

    return block1, block2