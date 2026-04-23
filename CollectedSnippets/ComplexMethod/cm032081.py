def format_file_summaries(self) -> str:
        """
        格式化文件总结内容，确保正确的标题层级并处理markdown文本
        """
        result = []
        # 首先对文件路径进行分组整理
        file_groups = {}
        for path in sorted(self.file_summaries_map.keys()):
            dir_path = os.path.dirname(path)
            if dir_path not in file_groups:
                file_groups[dir_path] = []
            file_groups[dir_path].append(path)

        # 处理没有目录的文件
        root_files = file_groups.get("", [])
        if root_files:
            for path in sorted(root_files):
                file_name = os.path.basename(path)
                result.append(f"\n📄 {file_name}")
                result.append(self.file_summaries_map[path])
                # 无目录的文件作为二级标题
                self._add_heading(f"📄 {file_name}", 2)
                # 使用convert_markdown_to_word处理文件内容
                self._add_content(convert_markdown_to_word(self.file_summaries_map[path]))
                self.doc.add_paragraph()

        # 处理有目录的文件
        for dir_path in sorted(file_groups.keys()):
            if dir_path == "":  # 跳过已处理的根目录文件
                continue

            # 添加目录作为二级标题
            result.append(f"\n📁 {dir_path}")
            self._add_heading(f"📁 {dir_path}", 2)

            # 该目录下的所有文件作为三级标题
            for path in sorted(file_groups[dir_path]):
                file_name = os.path.basename(path)
                result.append(f"\n📄 {file_name}")
                result.append(self.file_summaries_map[path])

                # 添加文件名作为三级标题
                self._add_heading(f"📄 {file_name}", 3)
                # 使用convert_markdown_to_word处理文件内容
                self._add_content(convert_markdown_to_word(self.file_summaries_map[path]))
                self.doc.add_paragraph()

        return "\n".join(result)