def excel_table_to_html(self, excel_table) -> str:
        """
        将 ExcelTable 转换为 HTML 表格字符串，保留合并单元格结构。
        """
        # 1. 创建坐标到单元格的映射，方便快速查找
        cell_map = {(c.row, c.col): c for c in excel_table.data}
        table_anchor = excel_table.anchor

        # 2. 用于记录已被合并单元格占据的位置，避免重复生成 td
        covered_cells = set()

        # 开始构建 HTML
        lines = ["<table>"]  # 可以根据需要添加样式类或属性

        for r in range(excel_table.num_rows):
            lines.append("  <tr>")
            for c in range(excel_table.num_cols):
                # 如果当前位置已被之前的合并单元格占据，则跳过
                if (r, c) in covered_cells:
                    continue

                # 获取当前位置的单元格
                cell = cell_map.get((r, c))

                if cell:
                    # 确定标签类型：第一行通常作为表头
                    tag = "th" if cell.row == 0 else "td"

                    # 构建属性列表 (rowspan, colspan)
                    attrs = []
                    if cell.row_span > 1:
                        attrs.append(f'rowspan="{cell.row_span}"')
                    if cell.col_span > 1:
                        attrs.append(f'colspan="{cell.col_span}"')

                    # 标记该单元格覆盖的所有位置为已占用
                    for ir in range(cell.row_span):
                        for ic in range(cell.col_span):
                            covered_cells.add((r + ir, c + ic))

                    # 拼接属性字符串
                    attr_str = " " + " ".join(attrs) if attrs else ""

                    # 生成 HTML 单元格，富文本片段避免二次转义
                    text_content = ""
                    if cell.text:
                        text_content = cell.text if cell.text_is_html else html.escape(cell.text)

                    # 添加媒体内容 (Images)
                    if cell.media:
                        media_content = "<br>".join(cell.media)
                        if text_content:
                            text_content += "<br>" + media_content
                        else:
                            text_content = media_content
                    # 添加公式
                    for formula in self._get_cell_math_formulas(
                        table_anchor,
                        excel_cell=cell,
                    ):
                        text_content += self.equation_bookends.format(EQ=formula)

                    inner_html = self._render_cell_inner_html(
                        text_content,
                        cell.text_is_html,
                    )
                    lines.append(f"    <{tag}{attr_str}>{inner_html}</{tag}>")
                else:
                    # 如果既没被覆盖，又没有数据对象（理论上 _find_table_bounds 逻辑应避免此情况），生成空单元格
                    lines.append("    <td></td>")

            lines.append("  </tr>")

        lines.append("</table>")
        return "\n".join(lines)