def _get_effective_list_marker(self, shape, paragraph) -> dict:
        """
        返回描述段落的有效列表标记的字典。
        列表标记信息可以来自多个来源：直接段落属性、形状级别的列表样式、
        布局占位符或主幻灯片文本样式。此辅助方法解析所有这些层，并返回
        有效标记的统一视图。

        Args:
            shape: 包含段落的形状对象。
            paragraph: 需要检查的'python-pptx'段落对象。

        Returns:
            返回列表标记信息的字典，其中：
            `is_list` - True/False/None，表示这是否是列表项；
            `kind` - 为以下之一：`buChar`、`buAutoNum`、`buBlip`、`buNone`或None，描述标记类型；
            `detail` - 项目符号字符或编号类型字符串，或如果不适用则为None；
            `level` - 段落级别，范围在(0, 8)内。
        """
        p = paragraph._element
        lvl = self._get_paragraph_level(p)

        # 1) 直接段落属性
        pPr = p.find("a:pPr", namespaces=self.namespaces)
        is_list, kind, detail = self._parse_bullet_from_paragraph_properties(pPr)
        if is_list is not None:
            return {
                "is_list": is_list,
                "kind": kind,
                "detail": detail,
                "level": lvl,
            }

        # 2) 形状级别的列表样式(txBody/a:lstStyle)
        txBody = shape._element.find(".//p:txBody", namespaces=self.namespaces)
        is_list, kind, detail = self._parse_bullet_from_text_body_list_style(
            txBody, lvl
        )
        if is_list is not None:
            return {
                "is_list": is_list,
                "kind": kind,
                "detail": detail,
                "level": lvl,
            }

        # 3) 布局占位符列表样式(如果这是一个占位符)
        layout_result = None
        if shape.is_placeholder:
            layout_ph = self._resolve_layout_placeholder(shape)

            if layout_ph is not None:
                layout_tx = layout_ph._element.find(
                    ".//p:txBody", namespaces=self.namespaces
                )
                is_list, kind, detail = self._parse_bullet_from_text_body_list_style(
                    layout_tx, lvl
                )

                # 仅在is_list明确为True/False时使用布局结果
                if is_list is not None:
                    layout_result = {
                        "is_list": is_list,
                        "kind": kind,
                        "detail": detail,
                        "level": lvl,
                    }

                # 4) 解析主文本样式
                ph_type = shape.placeholder_format.type
                master = shape.part.slide.slide_layout.slide_master
                is_list, kind, detail = self._parse_bullet_from_master_text_styles(
                    master, ph_type, lvl
                )

                # 检查主样式是否有标记信息
                if kind in ("buChar", "buAutoNum", "buBlip"):
                    return {
                        "is_list": True,
                        "kind": kind,
                        "detail": detail,
                        "level": lvl,
                    }
                elif is_list is not None:
                    return {
                        "is_list": is_list,
                        "kind": kind,
                        "detail": detail,
                        "level": lvl,
                    }

            # If layout has explicit is_list value but master didn't override it, use layout
            # 如果布局有显式的is_list值但主样式没有覆盖它，则使用布局结果
            if layout_result is not None:
                return layout_result

        return {
            "is_list": None,
            "kind": None,
            "detail": None,
            "level": lvl,
        }