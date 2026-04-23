def _normalize_table_colspans(self, html: str) -> str:
        """
        修正 HTML 表格中因无线表/少线表导致的 colspan 不一致问题。

        在无边框或少边框的 DOCX 表格中，部分行的单元格包含 w:gridSpan 值，
        该值来自 Word 内部虚拟栅格，并不反映实际视觉列数。mammoth 将这些
        w:gridSpan 值直接转换为 HTML colspan 属性，导致不同行的有效列数
        （所有 colspan 之和）不一致，产生行列对不齐的问题。

        本方法检测此类不一致，并将有效列数过多的行的 colspan 缩减至
        最常见的目标列数，从而恢复表格的正确结构。

        算法：
        1. 计算每行的有效列数（该行所有单元格 colspan 之和）
        2. 取最常见的列数作为目标列数
        3. 对有效列数超过目标值的行，从第一个 colspan > 1 的单元格开始缩减

        Args:
            html: 包含表格的 HTML 字符串

        Returns:
            str: 修正后的 HTML 字符串
        """
        try:
            from bs4 import BeautifulSoup
            from collections import Counter

            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            modified = False

            for table in tables:
                rows = table.find_all('tr')
                if not rows:
                    continue

                # 若表格中存在 rowspan > 1 的单元格，各行的显式 colspan 之和
                # 无法反映真实网格宽度（被 rowspan 占据的列不出现在后续行的 td
                # 列表中），此时算法的假设不成立，跳过该表格以避免误修改合法的
                # colspan。
                all_cells = table.find_all(['td', 'th'])
                if any(int(c.get('rowspan', 1)) > 1 for c in all_cells):
                    continue

                # 计算每行的有效列数（所有单元格的 colspan 之和）
                row_col_counts = []
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    total = sum(int(c.get('colspan', 1)) for c in cells)
                    row_col_counts.append(total)

                if not row_col_counts:
                    continue

                # 找到目标列数（出现最多的列数）
                count_freq = Counter(row_col_counts)
                if len(count_freq) == 1:
                    continue  # 各行列数已一致，无需修正

                target = count_freq.most_common(1)[0][0]

                # 修正有效列数超过目标值的行：缩减 colspan > 1 的单元格
                for row, col_count in zip(rows, row_col_counts):
                    if col_count <= target:
                        continue

                    excess = col_count - target
                    cells = row.find_all(['td', 'th'])

                    for cell in cells:
                        if excess <= 0:
                            break
                        span = int(cell.get('colspan', 1))
                        if span > 1:
                            reduce_by = min(span - 1, excess)
                            new_span = span - reduce_by
                            if new_span == 1:
                                if 'colspan' in cell.attrs:
                                    del cell['colspan']
                            else:
                                cell['colspan'] = str(new_span)
                            excess -= reduce_by
                            modified = True

            if modified:
                return str(soup)
            return html
        except Exception as e:
            logger.debug(f"Failed to normalize table colspans: {e}")
            return html