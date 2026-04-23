def __merge_2_vertical_text_blocks(block1, block2):
    if len(block1['lines']) > 0 and len(block2['lines']) > 0:
        first_line = block1['lines'][0]
        line_width = first_line['bbox'][2] - first_line['bbox'][0]
        block1_height = block1['bbox'][3] - block1['bbox'][1]
        block2_height = block2['bbox'][3] - block2['bbox'][1]
        min_block_height = min(block1_height, block2_height)
        if line_width > 0 and abs(block1['bbox_fs'][1] - first_line['bbox'][1]) < line_width / 2:
            last_line = block2['lines'][-1]
            if len(last_line['spans']) > 0:
                last_span = last_line['spans'][-1]
                line_width = last_line['bbox'][2] - last_line['bbox'][0]
                if line_width > 0 and len(first_line['spans']) > 0:
                    first_span = first_line['spans'][0]
                    first_content = first_span.get('content', '')
                    last_content = last_span.get('content', '')
                    if len(first_content) > 0:
                        span_start_with_num = first_content[0].isdigit()
                        span_start_with_big_char = first_content[0].isupper()
                        if (
                            abs(block2['bbox_fs'][3] - last_line['bbox'][3]) < line_width
                            and not last_content.endswith(LINE_STOP_FLAG)
                            and abs(block1_height - block2_height) < min_block_height
                            and not span_start_with_num
                            and not span_start_with_big_char
                        ):
                            if block1['page_num'] != block2['page_num']:
                                for line in block1['lines']:
                                    for span in line['spans']:
                                        span[SplitFlag.CROSS_PAGE] = True
                            block2['lines'].extend(block1['lines'])
                            block1['lines'] = []
                            block1[SplitFlag.LINES_DELETED] = True

    return block1, block2