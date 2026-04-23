def _build_section_hierarchy(self, sections: List[PaperSection]) -> List[PaperSection]:
        """构建章节的层次结构"""
        if not sections:
            return []

        # 按层级排序
        root_sections = []
        current_parents = {0: None}  # 每个层级的当前父节点

        for section in sections:
            # 找到当前节点的父节点
            parent_level = None
            for level in sorted([k for k in current_parents.keys() if k < section.level], reverse=True):
                parent_level = level
                break

            if parent_level is None:
                # 顶级节点
                root_sections.append(section)
            else:
                # 添加为子节点
                parent = current_parents[parent_level]
                if parent:
                    parent.subsections.append(section)
                else:
                    root_sections.append(section)

            # 更新当前层级的父节点
            current_parents[section.level] = section

            # 清除所有更深层级的父节点缓存
            deeper_levels = [k for k in current_parents.keys() if k > section.level]
            for level in deeper_levels:
                current_parents.pop(level, None)

        return root_sections