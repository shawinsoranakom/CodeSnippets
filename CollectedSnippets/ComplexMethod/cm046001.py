def merge_para_with_text_v2(para_block):
    block_text = ''
    for line in para_block['lines']:
        for span in line['spans']:
            if span['type'] in [ContentType.TEXT]:
                span['content'] = full_to_half_exclude_marks(span['content'])
                block_text += span['content']
    block_lang = detect_lang(block_text)

    para_content = []
    para_type = para_block['type']
    for i, line in enumerate(para_block['lines']):
        for j, span in enumerate(line['spans']):
            span_type = span['type']
            if span.get("content", '').strip():
                if span_type == ContentType.TEXT:
                    if para_type == BlockType.PHONETIC:
                        span_type = ContentTypeV2.SPAN_PHONETIC
                    else:
                        span_type = ContentTypeV2.SPAN_TEXT
                if span_type == ContentType.INLINE_EQUATION:
                    span_type = ContentTypeV2.SPAN_EQUATION_INLINE
                if span_type in [
                    ContentTypeV2.SPAN_TEXT,
                ]:
                    # 定义CJK语言集合(中日韩)
                    cjk_langs = {'zh', 'ja', 'ko'}
                    # logger.info(f'block_lang: {block_lang}, content: {content}')

                    # 判断是否为行末span
                    is_last_span = j == len(line['spans']) - 1

                    if block_lang in cjk_langs:  # 中文/日语/韩文语境下，换行不需要空格分隔,但是如果是行内公式结尾，还是要加空格
                        if is_last_span:
                            span_content = span['content']
                        else:
                            span_content = f"{span['content']} "
                    else:
                        # 如果span是line的最后一个且末尾带有-连字符，那么末尾不应该加空格,同时应该把-删除
                        if (
                                is_last_span
                                and is_hyphen_at_line_end(span['content'])
                        ):
                            # 如果下一行的第一个span是小写字母开头，删除连字符
                            if (
                                    i + 1 < len(para_block['lines'])
                                    and para_block['lines'][i + 1].get('spans')
                                    and para_block['lines'][i + 1]['spans'][0].get('type') == ContentType.TEXT
                                    and para_block['lines'][i + 1]['spans'][0].get('content', '')
                                    and para_block['lines'][i + 1]['spans'][0]['content'][0].islower()
                            ):
                                span_content = span['content'][:-1]
                            else:  # 如果没有下一行，或者下一行的第一个span不是小写字母开头，则保留连字符但不加空格
                                span_content = span['content']
                        else:
                            # 西方文本语境下content间需要空格分隔
                            span_content = f"{span['content']} "

                    if para_content and para_content[-1]['type'] == span_type:
                        # 合并相同类型的span
                        para_content[-1]['content'] += span_content
                    else:
                        span_content = {
                            'type': span_type,
                            'content': span_content,
                        }
                        para_content.append(span_content)

                elif span_type in [
                    ContentTypeV2.SPAN_PHONETIC,
                    ContentTypeV2.SPAN_EQUATION_INLINE,
                ]:
                    span_content = {
                        'type': span_type,
                        'content': span['content'],
                    }
                    para_content.append(span_content)
                else:
                    logger.warning(f"Unknown span type in merge_para_with_text_v2: {span_type}")
    return para_content