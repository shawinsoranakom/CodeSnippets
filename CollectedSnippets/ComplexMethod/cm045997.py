def merge_para_with_text(
    para_block,
    formula_enable=True,
    img_buket_path='',
    escape_text_block_prefix=True,
):
    block_text = ''
    for line in para_block['lines']:
        for span in line['spans']:
            if span['type'] in [ContentType.TEXT]:
                span['content'] = full_to_half_exclude_marks(span['content'])
                block_text += span['content']
    block_lang = detect_lang(block_text)
    escape_markdown_text = para_block.get('type') != BlockType.CODE_BODY

    para_text = ''
    for i, line in enumerate(para_block['lines']):
        for j, span in enumerate(line['spans']):
            span_type = span['type']
            content = ''
            if span_type == ContentType.TEXT:
                content = span['content']
                if escape_markdown_text:
                    content = escape_conservative_markdown_text(content)
            elif span_type == ContentType.INLINE_EQUATION:
                content = f"{inline_left_delimiter}{span['content']}{inline_right_delimiter}"
            elif span_type == ContentType.INTERLINE_EQUATION:
                if formula_enable:
                    content = f"\n{display_left_delimiter}\n{span['content']}\n{display_right_delimiter}\n"
                else:
                    if span.get('image_path', ''):
                        content = f"![]({img_buket_path}/{span['image_path']})"

            content = content.strip()
            if content:

                if span_type == ContentType.INTERLINE_EQUATION:
                    para_text += content
                    continue

                # 定义CJK语言集合(中日韩)
                cjk_langs = {'zh', 'ja', 'ko'}
                # logger.info(f'block_lang: {block_lang}, content: {content}')

                # 判断是否为行末span
                is_last_span = j == len(line['spans']) - 1

                if block_lang in cjk_langs:  # 中文/日语/韩文语境下，换行不需要空格分隔,但是如果是行内公式结尾，还是要加空格
                    if is_last_span and span_type != ContentType.INLINE_EQUATION:
                        para_text += content
                    else:
                        para_text += f'{content} '
                else:
                    # 西方文本语境下 每行的最后一个span判断是否要去除连字符
                    if span_type in [ContentType.TEXT, ContentType.INLINE_EQUATION]:
                        # 如果span是line的最后一个且末尾带有-连字符，那么末尾不应该加空格,同时应该把-删除
                        if (
                                is_last_span
                                and span_type == ContentType.TEXT
                                and is_hyphen_at_line_end(content)
                        ):
                            # 如果下一行的第一个span是小写字母开头，删除连字符
                            if (
                                    i+1 < len(para_block['lines'])
                                    and para_block['lines'][i + 1].get('spans')
                                    and para_block['lines'][i + 1]['spans'][0].get('type') == ContentType.TEXT
                                    and para_block['lines'][i + 1]['spans'][0].get('content', '')
                                    and para_block['lines'][i + 1]['spans'][0]['content'][0].islower()
                            ):
                                para_text += content[:-1]
                            else:  # 如果没有下一行，或者下一行的第一个span不是小写字母开头，则保留连字符但不加空格
                                para_text += content
                        else:  # 西方文本语境下 content间需要空格分隔
                            para_text += f'{content} '
    if escape_text_block_prefix and para_block.get('type') == BlockType.TEXT:
        para_text = escape_text_block_markdown_prefix(para_text)
    return para_text