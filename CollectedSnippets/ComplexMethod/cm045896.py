def _add_list_item(
        self,
        *,
        numid: int,
        ilevel: int,
        elements: list,
        is_numbered: bool = False,
        text: str = "",
        equations: list = None,
    ) -> list:
        """
        添加列表项。

        生成的列表结构：
        {
            "type": "list",
            "attribute": "ordered" / "unordered",
            "ilevel": 0,
            "content": [
                {"type": "text", "content": "列表项文本"},
                {"type": "list", "attribute": "...", "ilevel": 1, "content": [...]},
                {"type": "text", "content": "另一个列表项"}
            ]
        }

        Args:
            numid: 列表ID
            ilevel: 缩进等级
            elements: 元素列表
            is_numbered: 是否编号
            text: 处理后的文本（包含公式标记）
            equations: 公式列表

        Returns:
            list[RefItem]: 元素引用列表
        """
        if equations is None:
            equations = []
        if not elements:
            return None

        # 构建 content_text，处理行内公式和超链接
        content_text = self._build_text_with_equations_and_hyperlinks(
            elements, text, equations
        )

        # 确定列表属性
        list_attribute = "ordered" if is_numbered else "unordered"

        # 情况 1: 不存在上一个列表ID，或遇到了不同 numId 的新列表，创建新的顶层列表
        if self.pre_num_id == -1 or self.pre_num_id != numid:
            # 切换到不同的列表时，先重置旧列表状态
            if self.pre_num_id != -1:
                self.pre_num_id = -1
                self.pre_ilevel = -1
                self.list_block_stack = []
                self.list_counters = {}
            # 为新编号序列重置计数器，确保编号从1开始
            self._reset_list_counters_for_new_sequence(numid)

            list_block = {
                "type": BlockType.LIST,
                "attribute": list_attribute,
                "content": [],
                "ilevel": ilevel,
            }
            self.cur_page.append(list_block)
            # 入栈, 记录当前的列表块
            self.list_block_stack.append(list_block)

            list_item = {
                "type": BlockType.TEXT,
                "content": content_text,
            }

            list_block["content"].append(list_item)
            self.pre_num_id = numid
            self.pre_ilevel = ilevel

        # 情况 2: 增加缩进，打开子列表
        elif (
            self.pre_num_id == numid  # 同一个列表
            and self.pre_ilevel != -1  # 上一个缩进级别已知
            and self.pre_ilevel < ilevel  # 当前层级比之前更缩进
        ):
            # 创建新的子列表块
            child_list_block = {
                "type": BlockType.LIST,
                "attribute": list_attribute,
                "content": [],
                "ilevel": ilevel,
            }

            # 获取栈顶的列表块，将子列表直接添加到其content中
            parent_list_block = self.list_block_stack[-1]
            parent_list_block["content"].append(child_list_block)

            # 入栈, 记录当前的列表块
            self.list_block_stack.append(child_list_block)

            # 添加当前列表项到子列表
            list_item = {
                "type": BlockType.TEXT,
                "content": content_text,
            }
            child_list_block["content"].append(list_item)

            # 更新目前缩进
            self.pre_ilevel = ilevel

        # 情况3: 减少缩进，关闭子列表
        elif (
            self.pre_num_id == numid  # 同一个列表
            and self.pre_ilevel != -1  # 上一个缩进级别已知
            and ilevel < self.pre_ilevel  # 当前层级比之前更少缩进
        ):
            # 出栈，直到找到匹配的 ilevel
            while self.list_block_stack:
                top_list_block = self.list_block_stack[-1]
                if top_list_block["ilevel"] == ilevel:
                    break
                self.list_block_stack.pop()
            list_block = self.list_block_stack[-1]

            list_item = {
                "type": BlockType.TEXT,
                "content": content_text,
            }
            list_block["content"].append(list_item)
            self.pre_ilevel = ilevel

        # 情况 4: 同级列表项（相同缩进）
        elif self.pre_num_id == numid and self.pre_ilevel == ilevel:
            # 获取栈顶的列表块
            list_block = self.list_block_stack[-1]


            list_item = {
                "type": BlockType.TEXT,
                "content": content_text,
            }
            list_block["content"].append(list_item)

        else:
            logger.warning(
                "Unexpected DOCX list state in _add_list_item: "
                f"pre_num_id={self.pre_num_id}, numid={numid}, "
                f"pre_ilevel={self.pre_ilevel}, ilevel={ilevel}, "
                f"stack_depth={len(self.list_block_stack)}. "
            )