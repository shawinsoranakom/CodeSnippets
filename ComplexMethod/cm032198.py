def _markdown_to_html(self, text):
        """将Markdown格式转换为HTML格式，保留文档结构"""
        try:
            import markdown
            # 使用Python-Markdown库将markdown转换为HTML，启用更多扩展以支持嵌套列表
            return markdown.markdown(text, extensions=['tables', 'fenced_code', 'codehilite', 'nl2br', 'sane_lists', 'smarty', 'extra'])
        except ImportError:
            # 如果没有markdown库，使用更复杂的替换来处理嵌套列表
            import re

            # 替换标题
            text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
            text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
            text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)

            # 预处理列表 - 在列表项之间添加空行以正确分隔
            # 处理编号列表
            text = re.sub(r'(\n\d+\.\s.+)(\n\d+\.\s)', r'\1\n\2', text)
            # 处理项目符号列表
            text = re.sub(r'(\n•\s.+)(\n•\s)', r'\1\n\2', text)
            text = re.sub(r'(\n\*\s.+)(\n\*\s)', r'\1\n\2', text)
            text = re.sub(r'(\n-\s.+)(\n-\s)', r'\1\n\2', text)

            # 处理嵌套列表 - 确保正确的缩进和结构
            lines = text.split('\n')
            in_list = False
            list_type = None  # 'ol' 或 'ul'
            list_html = []
            normal_lines = []

            i = 0
            while i < len(lines):
                line = lines[i]

                # 匹配编号列表项
                numbered_match = re.match(r'^(\d+)\.\s+(.+)$', line)
                # 匹配项目符号列表项
                bullet_match = re.match(r'^[•\*-]\s+(.+)$', line)

                if numbered_match:
                    if not in_list or list_type != 'ol':
                        # 开始新的编号列表
                        if in_list:
                            # 关闭前一个列表
                            list_html.append(f'</{list_type}>')
                        list_html.append('<ol>')
                        in_list = True
                        list_type = 'ol'

                    num, content = numbered_match.groups()
                    list_html.append(f'<li>{content}</li>')

                elif bullet_match:
                    if not in_list or list_type != 'ul':
                        # 开始新的项目符号列表
                        if in_list:
                            # 关闭前一个列表
                            list_html.append(f'</{list_type}>')
                        list_html.append('<ul>')
                        in_list = True
                        list_type = 'ul'

                    content = bullet_match.group(1)
                    list_html.append(f'<li>{content}</li>')

                else:
                    if in_list:
                        # 结束当前列表
                        list_html.append(f'</{list_type}>')
                        in_list = False
                        # 将完成的列表添加到正常行中
                        normal_lines.append(''.join(list_html))
                        list_html = []

                    normal_lines.append(line)

                i += 1

            # 如果最后还在列表中，确保关闭列表
            if in_list:
                list_html.append(f'</{list_type}>')
                normal_lines.append(''.join(list_html))

            # 重建文本
            text = '\n'.join(normal_lines)

            # 替换段落，但避免处理已经是HTML标签的部分
            paragraphs = text.split('\n\n')
            for i, p in enumerate(paragraphs):
                # 如果不是以HTML标签开始且不为空
                if not (p.strip().startswith('<') and p.strip().endswith('>')) and p.strip() != '':
                    paragraphs[i] = f'<p>{p}</p>'

            return '\n'.join(paragraphs)