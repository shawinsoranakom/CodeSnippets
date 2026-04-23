def _get_paragraph_position(self, paragraph_element):
        """
        从段落元素提取垂直位置信息。
        """
        # 先尝试直接从包含顺序相关属性的 w:p 元素获取索引
        if (
            hasattr(paragraph_element, "getparent")
            and paragraph_element.getparent() is not None
        ):
            parent = paragraph_element.getparent()
            # 获取所有段落兄弟节点
            paragraphs = [
                p for p in parent.getchildren() if etree.QName(p).localname == "p"
            ]
            # 查找当前段落在其兄弟节点中的索引
            try:
                paragraph_index = paragraphs.index(paragraph_element)
                return paragraph_index  # 使用索引作为位置以保证一致的排序
            except ValueError:
                pass

        # 在元素及其祖先中查找位置提示属性
        for elem in (*[paragraph_element], *paragraph_element.iterancestors()):
            # 检查直接的位置信息属性
            for attr_name in ["y", "top", "positionY", "y-position", "position"]:
                value = elem.get(attr_name)
                if value:
                    try:
                        # 移除任何非数字字符（如 'pt', 'px' 等）
                        clean_value = re.sub(r"[^0-9.]", "", value)
                        if clean_value:
                            return float(clean_value)
                    except (ValueError, TypeError):
                        pass

            # 检查 transform 属性中的位移信息
            transform = elem.get("transform")
            if transform:
                # 从 transform 矩阵中提取 translate 的第二个参数
                match = re.search(r"translate\([^,]+,\s*([0-9.]+)", transform)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        pass

            # 检查 Word 格式中的锚点或相对位置指示器
            # 'dist' 类属性可以表示相对位置
            for attr_name in ["distT", "distB", "anchor", "relativeFrom"]:
                if elem.get(attr_name) is not None:
                    return elem.sourceline  # 使用 XML 源行号作为回退

        # 针对 VML 形状，查找特定属性
        for ns_uri in paragraph_element.nsmap.values():
            if "vml" in ns_uri:
                # 尝试从 style 属性提取 top 值
                style = paragraph_element.get("style")
                if style:
                    match = re.search(r"top:([0-9.]+)pt", style)
                    if match:
                        try:
                            return float(match.group(1))
                        except ValueError:
                            pass

        # 如果没有更好的位置指示，则使用 XML 源行号作为顺序的代理
        return (
            paragraph_element.sourceline
            if hasattr(paragraph_element, "sourceline")
            else None
        )