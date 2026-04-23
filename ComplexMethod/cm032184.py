def generate_markdown(self, doc: StructuredDocument) -> str:
        """将结构化文档转换为Markdown格式

        Args:
            doc: 结构化文档对象

        Returns:
            str: Markdown格式文本
        """
        md_parts = []

        # 添加标题
        if doc.title:
            md_parts.append(f"# {doc.title}\n")

        # 添加元数据
        if doc.is_paper:
            # 作者信息
            if 'authors' in doc.metadata and doc.metadata['authors']:
                authors_str = ", ".join(doc.metadata['authors'])
                md_parts.append(f"**作者:** {authors_str}\n")

            # 关键词
            if 'keywords' in doc.metadata and doc.metadata['keywords']:
                keywords_str = ", ".join(doc.metadata['keywords'])
                md_parts.append(f"**关键词:** {keywords_str}\n")

            # 摘要
            if 'abstract' in doc.metadata and doc.metadata['abstract']:
                md_parts.append(f"## 摘要\n\n{doc.metadata['abstract']}\n")

        # 添加章节内容
        md_parts.append(self._format_sections_markdown(doc.sections))

        return "\n".join(md_parts)