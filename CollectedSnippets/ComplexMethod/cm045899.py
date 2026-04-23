def _add_index_item(
        self,
        *,
        ilevel: int,
        elements: list,
        text: str = "",
        equations: list = None,
        anchor: Optional[str] = None,
    ) -> None:
        """
        添加目录项到索引块。

        生成的索引结构：
        {
            "type": "index",
            "ilevel": 0,
            "content": [
                {"type": "text", "content": "目录项文本"},
                {"type": "index", "ilevel": 1, "content": [...]},
            ]
        }

        Args:
            ilevel: 缩进等级（0-based）
            elements: 元素列表
            text: 处理后的文本（包含公式标记）
            equations: 公式列表
        """
        if equations is None:
            equations = []
        if not elements:
            return

        content_text = self._build_text_with_equations_and_hyperlinks(
            elements, text, equations
        )

        # 情况 1: 首个目录项，创建新的顶层索引块
        if self.pre_index_ilevel == -1:
            index_block = {
                "type": BlockType.INDEX,
                "content": [],
                "ilevel": ilevel,
            }
            self.cur_page.append(index_block)
            self.index_block_stack.append(index_block)

            index_item = {
                "type": BlockType.TEXT,
                "content": content_text,
            }
            if anchor:
                index_item["anchor"] = anchor
            index_block["content"].append(index_item)
            self.pre_index_ilevel = ilevel

        # 情况 2: 增加缩进，打开子索引块
        elif self.pre_index_ilevel < ilevel:
            child_index_block = {
                "type": BlockType.INDEX,
                "content": [],
                "ilevel": ilevel,
            }
            parent_index_block = self.index_block_stack[-1]
            parent_index_block["content"].append(child_index_block)
            self.index_block_stack.append(child_index_block)

            index_item = {
                "type": BlockType.TEXT,
                "content": content_text,
            }
            if anchor:
                index_item["anchor"] = anchor
            child_index_block["content"].append(index_item)
            self.pre_index_ilevel = ilevel

        # 情况 3: 减少缩进，关闭子索引块
        elif ilevel < self.pre_index_ilevel:
            while self.index_block_stack:
                top_block = self.index_block_stack[-1]
                if top_block["ilevel"] == ilevel:
                    break
                self.index_block_stack.pop()
            if self.index_block_stack:
                index_block = self.index_block_stack[-1]
                index_item = {
                    "type": BlockType.TEXT,
                    "content": content_text,
                }
                if anchor:
                    index_item["anchor"] = anchor
                index_block["content"].append(index_item)
            self.pre_index_ilevel = ilevel

        # 情况 4: 同级目录项
        else:
            if self.index_block_stack:
                index_block = self.index_block_stack[-1]
                index_item = {
                    "type": BlockType.TEXT,
                    "content": content_text,
                }
                if anchor:
                    index_item["anchor"] = anchor
                index_block["content"].append(index_item)