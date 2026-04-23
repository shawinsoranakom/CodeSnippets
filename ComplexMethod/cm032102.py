def _extract_figures_and_tables(self, elements) -> Tuple[List[Figure], List[Figure]]:
        """提取文档中的图表信息"""
        figures = []
        tables = []

        for i, element in enumerate(elements):
            element_text = str(element).strip()

            # 查找图表标识
            fig_match = re.match(r'^(figure|fig\.|图)\s*(\d+)[.:](.*)', element_text, re.IGNORECASE)
            table_match = re.match(r'^(table|表)\s*(\d+)[.:](.*)', element_text, re.IGNORECASE)

            if fig_match:
                fig_id = f"{fig_match.group(1)} {fig_match.group(2)}"
                caption = fig_match.group(3).strip()

                # 查找图表描述（通常在图表标识下方）
                description = ""
                for j in range(i+1, min(i+5, len(elements))):
                    next_text = str(elements[j]).strip()
                    if isinstance(elements[j], (Title, Table)) or re.match(r'^(figure|fig\.|table|图|表)\s*\d+', next_text, re.IGNORECASE):
                        break
                    description += next_text + " "

                figures.append(Figure(
                    id=fig_id,
                    caption=caption,
                    content=description.strip(),
                    position=i
                ))

            elif table_match:
                table_id = f"{table_match.group(1)} {table_match.group(2)}"
                caption = table_match.group(3).strip()

                # 对于表格，尝试获取表格内容
                table_content = ""
                if i+1 < len(elements) and isinstance(elements[i+1], Table):
                    table_content = str(elements[i+1])

                tables.append(Figure(
                    id=table_id,
                    caption=caption,
                    content=table_content,
                    position=i
                ))

            # 检查元素本身是否为表格
            elif isinstance(element, Table):
                # 查找表格标题（通常在表格之前）
                caption = ""
                if i > 0:
                    prev_text = str(elements[i-1]).strip()
                    if re.match(r'^(table|表)\s*\d+', prev_text, re.IGNORECASE):
                        caption = prev_text

                if not caption:
                    caption = f"Table {len(tables) + 1}"

                tables.append(Figure(
                    id=f"Table {len(tables) + 1}",
                    caption=caption,
                    content=element_text,
                    position=i
                ))

            # 检查元素本身是否为图片
            elif isinstance(element, Image):
                # 查找图片标题（通常在图片之前或之后）
                caption = ""
                for j in range(max(0, i-2), min(i+3, len(elements))):
                    if j != i:
                        j_text = str(elements[j]).strip()
                        if re.match(r'^(figure|fig\.|图)\s*\d+', j_text, re.IGNORECASE):
                            caption = j_text
                            break

                if not caption:
                    caption = f"Figure {len(figures) + 1}"

                figures.append(Figure(
                    id=f"Figure {len(figures) + 1}",
                    caption=caption,
                    content="[Image]",
                    position=i
                ))

        return figures, tables