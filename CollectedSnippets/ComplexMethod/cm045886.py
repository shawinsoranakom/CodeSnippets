def _inject_equations_into_table(self, html_table, xml_table):
        """
        将 DOCX XML 表格中的 OMML 公式注入到 mammoth 生成的 HTML 表格中。

        mammoth 会静默丢弃 OMML（Office Math Markup Language）公式，导致含公式
        的表格单元格在 HTML 中为空。本方法并行遍历 HTML 表格（BeautifulSoup 对象）
        和 XML 表格（lxml 元素），对含有 OMML 公式的单元格用包含公式占位符的内容
        替换原来的空内容。

        Args:
            html_table: BeautifulSoup 的 Tag 对象，代表 mammoth 生成的 <table> 元素
            xml_table: lxml 的 Element 对象，代表原始 DOCX 中对应的 <w:tbl> 元素

        Returns:
            BeautifulSoup Tag: 注入公式后的 <table> 元素（原地修改并返回）
        """
        OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
        W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        # 快速检查：该表格是否含有任何公式
        if not xml_table.findall(f".//{{{OMML_NS}}}oMath"):
            return html_table

        from bs4 import BeautifulSoup

        html_rows = html_table.find_all('tr')
        xml_rows = xml_table.findall(f"{{{W_NS}}}tr")

        if len(html_rows) != len(xml_rows):
            logger.debug(
                f"Table row count mismatch when injecting equations: "
                f"HTML {len(html_rows)} vs XML {len(xml_rows)}"
            )
            return html_table

        for html_row, xml_row in zip(html_rows, xml_rows):
            html_cells = html_row.find_all(['td', 'th'])
            xml_cells = xml_row.findall(f"{{{W_NS}}}tc")

            if len(html_cells) != len(xml_cells):
                continue

            for html_cell, xml_cell in zip(html_cells, xml_cells):
                if not xml_cell.findall(f".//{{{OMML_NS}}}oMath"):
                    continue

                # 该单元格含公式，重建其 HTML 内容以保留公式
                new_content = self._build_cell_html_with_equations(xml_cell)
                if new_content:
                    html_cell.clear()
                    new_soup = BeautifulSoup(new_content, 'html.parser')
                    for child in list(new_soup.children):
                        html_cell.append(child)

        return html_table