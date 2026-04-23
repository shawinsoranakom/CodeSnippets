def clean_tag(match):
        """清洗单个标签，只保留结构相关的属性"""
        full_tag = match.group(0)
        tag_name = match.group(1).lower()

        # 自闭合标签的处理
        is_self_closing = full_tag.rstrip().endswith('/>')

        # img 标签额外保留图片相关属性（如内联 base64 src）
        current_preserved = preserved_attrs | (img_preserved_attrs if tag_name == 'img' else set())

        # 提取需要保留的属性
        kept_attrs = []

        # 匹配所有属性: attr="value" 或 attr='value' 或 attr=value 或单独的attr
        attr_pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))|(\w+)(?=\s|>|/>)'
        for attr_match in re.finditer(attr_pattern, full_tag):
            if attr_match.group(5):
                # 单独的属性（如 disabled），跳过
                continue

            attr_name = attr_match.group(1)
            if attr_name is None:
                continue
            attr_name = attr_name.lower()
            attr_value = attr_match.group(2) or attr_match.group(3) or attr_match.group(4) or ""

            # 只保留指定属性（表格结构属性，img 标签还额外保留图片内容属性）
            if attr_name in current_preserved:
                kept_attrs.append(f'{attr_name}="{attr_value}"')

        # 重建标签
        if kept_attrs:
            attrs_str = ' ' + ' '.join(kept_attrs)
        else:
            attrs_str = ''

        if is_self_closing:
            return f'<{tag_name}{attrs_str}/>'
        else:
            return f'<{tag_name}{attrs_str}>'