def _build_paragraph_html_with_equations(self, xml_para) -> Optional[str]:
        """
        为可能含 OMML 公式的段落构建 HTML 字符串。

        使用与 _handle_equations_in_text 相同的迭代逻辑：
        - 普通 <w:t> 元素的文本直接收集
        - <m:oMath> 元素转换为 LaTeX 并包装为公式占位符 <eq>...</eq>
        - <m:t> 等 math 命名空间下的 <t> 元素因标签中含 "math" 而被跳过，
          避免在 oMath2Latex 已处理整个 oMath 子树后重复提取

        Args:
            xml_para: lxml Element，代表 DOCX 中的 <w:p> 元素

        Returns:
            str | None: 格式为 "<p>...</p>" 的 HTML 字符串；段落为空时返回 None
        """
        items = []
        for subt in xml_para.iter():
            tag_name = etree.QName(subt).localname
            # 普通文本节点（排除 math 命名空间下的 <m:t>）
            if tag_name == 't' and 'math' not in subt.tag:
                if isinstance(subt.text, str) and subt.text:
                    items.append(subt.text)
            # OMML 公式元素（排除 oMathPara 容器避免重复处理）
            elif 'oMath' in subt.tag and 'oMathPara' not in subt.tag:
                try:
                    latex = str(oMath2Latex(subt)).strip()
                    if latex:
                        items.append(self.equation_bookends.format(EQ=latex))
                except Exception as e:
                    logger.debug(f"Failed to convert OMML equation to LaTeX: {e}")

        if not items:
            return None
        return f'<p>{"".join(items)}</p>'