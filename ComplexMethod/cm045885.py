def _preparse_tables_with_mammoth(self, file_bytes: bytes) -> list:
        """
        使用 mammoth 完整文档转换预解析所有顶层表格的 HTML。

        孤立模式下（仅传入 <w:tbl> XML 片段），mammoth 缺少编号定义
        （word/numbering.xml）、样式（word/styles.xml）和关系
        （word/_rels/document.xml.rels）等上下文，在遇到含列表项或图片
        的单元格时会抛出 AttributeError。通过完整文档转换，mammoth 可
        获得完整上下文，从而正确处理这些情况。

        图片会被 mammoth 转换为内联 data-URI base64 格式（<img src="data:...">）。

        注意：mammoth 不支持 OMML（Office Math Markup Language）公式，会静默丢弃
        表格单元格内的公式。本方法在获取 mammoth HTML 后，会同步遍历原始 DOCX XML，
        将丢失的公式重新注入对应的 HTML 单元格。

        Returns:
            list[str]: 文档中所有顶层表格的 HTML 字符串列表，按文档顺序排列
        """
        try:
            import mammoth as _mammoth
            from bs4 import BeautifulSoup as _BeautifulSoup

            result = _mammoth.convert_to_html(BytesIO(file_bytes))
            soup = _BeautifulSoup(result.value, 'html.parser')

            # 仅保留顶层表格，排除嵌套在其他表格单元格内的子表格
            all_tables = soup.find_all('table')
            top_level_tables = [t for t in all_tables if not t.find_parent('table')]

            # 同步加载 DOCX XML，获取所有顶层表格元素，用于公式注入
            docx_obj = Document(BytesIO(file_bytes))
            xml_top_tables = [
                elem for elem in docx_obj.element.body
                if etree.QName(elem).localname == 'tbl'
            ]

            logger.debug(
                f"Pre-parsed {len(top_level_tables)} top-level tables via full mammoth conversion"
            )

            # 将 XML 表格中的 OMML 公式注入到 mammoth HTML 表格中
            result_tables = []
            for idx, html_table in enumerate(top_level_tables):
                if idx < len(xml_top_tables):
                    html_table = self._inject_equations_into_table(
                        html_table, xml_top_tables[idx]
                    )
                result_tables.append(str(html_table))
            return result_tables
        except Exception as e:
            logger.debug(f"Could not pre-parse tables with full mammoth conversion: {e}")
            return []