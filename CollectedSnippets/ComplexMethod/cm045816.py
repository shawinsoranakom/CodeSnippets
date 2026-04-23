def _is_list_item(self, paragraph) -> tuple[bool, str]:
        """
        判断段落是否应被视为列表项。
        该方法首先尝试通过拥有该段落的形状来解析列表样式信息。
        如果无法做到，则回退到基于段落属性和级别的更简单检查。
        Args:
            paragraph: 需要检查的'python-pptx'段落对象。

        Returns:
            返回一个2元组(`is_list`, `bullet_type`)，其中：
            `is_list` - 若段落被视为列表项，为True，否则为False；
            `bullet_type` - 为以下之一：'Bullet'(项目符号)、'Numbered'(编号)或'None'，
            描述列表标记类型。
        """
        # 尝试从段落获取形状（包含该段落的对象），如果可能的话
        shape = None
        try:
            # 这个路径适用于python-pptx段落对象
            # 首先获取文本框架(段落的父对象)
            text_frame = paragraph._parent
            # 然后获取形状(文本框架的父对象)
            shape = text_frame._parent
        except AttributeError:
            pass

        if shape is not None:
            list_info = self._get_paragraph_list_info(shape, paragraph)
            if not list_info["is_list"]:
                return (False, "None")

            if list_info["attribute"] == "ordered":
                return (True, "Numbered")
            return (True, "Bullet")

        # 如果无法获取形状，使用更简单的检查方式
        p = paragraph._element
        if p.find(".//a:buChar", namespaces={"a": self.namespaces["a"]}) is not None:
            return (True, "Bullet")
        elif (
            p.find(".//a:buAutoNum", namespaces={"a": self.namespaces["a"]}) is not None
        ):
            return (True, "Numbered")
        elif paragraph.level > 0:
            # 很可能是子列表项(缩进表示嵌套)
            return (True, "None")
        else:
            return (False, "None")