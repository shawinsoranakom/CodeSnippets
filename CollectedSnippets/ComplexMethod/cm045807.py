def _handle_tables(self, shape):
        """将PowerPoint表格转换为HTML格式。

        Args:
            shape: 包含表格的形状对象。
            parent_slide: 父幻灯片组。
            slide_ind: 当前幻灯片索引。
            doc: 文档对象(此实现中未使用)。
            slide_size: 幻灯片尺寸。

        Returns:
            str: 表格的HTML字符串，如果没有表格则返回None。
        """
        if not shape.has_table:
            return None

        table = shape.table
        table_xml = shape._element

        # 开始构建HTML表格
        html_parts = ['<table border="1">']

        # 跟踪已被合并单元格占用的位置
        # 格式: {(row, col): True}
        occupied_cells = {}

        for row_idx, row in enumerate(table.rows):
            html_parts.append("  <tr>")

            for col_idx, cell in enumerate(row.cells):
                # 跳过被合并占用的单元格
                if (row_idx, col_idx) in occupied_cells:
                    continue
                # 获取单元格XML以读取跨度信息
                cell_xml = table_xml.xpath(
                    f".//a:tbl/a:tr[{row_idx + 1}]/a:tc[{col_idx + 1}]"
                )

                if not cell_xml:
                    continue

                cell_xml = cell_xml[0]

                # 解析行跨度和列跨度
                row_span = cell_xml.get("rowSpan")
                col_span = cell_xml.get("gridSpan")

                row_span = int(row_span) if row_span else 1
                col_span = int(col_span) if col_span else 1

                # 标记被此单元格占用的位置
                for r in range(row_idx, row_idx + row_span):
                    for c in range(col_idx, col_idx + col_span):
                        if (r, c) != (row_idx, col_idx):
                            occupied_cells[(r, c)] = True

                # 确定标签类型：第一行使用<th>，其他使用<td>
                tag = "th" if row_idx == 0 else "td"

                # 构建属性字符串
                attrs = []
                if row_span > 1:
                    attrs.append(f'rowspan="{row_span}"')
                if col_span > 1:
                    attrs.append(f'colspan="{col_span}"')

                attr_str = " " + " ".join(attrs) if attrs else ""

                # 获取单元格文本内容
                cell_text = cell.text.strip() if cell.text else ""
                # 转义HTML特殊字符，防止XSS
                cell_text = (
                    cell_text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )

                html_parts.append(f"    <{tag}{attr_str}>{cell_text}</{tag}>")

            html_parts.append("  </tr>")

        html_parts.append("</table>")

        self.cur_page.append(
            {
                "type": BlockType.TABLE,
                "content": "\n".join(html_parts),
            }
        )

        return None