def generate_markdown(self, paper: StructuredPaper) -> str:
        """将论文结构化数据转换为Markdown格式

        Args:
            paper: 结构化论文数据对象

        Returns:
            str: 完整的Markdown格式论文文本
        """
        md_parts = []

        # 标题和作者信息
        md_parts.append(f"# {paper.metadata.title}\n")

        if paper.metadata.authors:
            authors_str = ", ".join(paper.metadata.authors)
            md_parts.append(f"**作者:** {authors_str}\n")

        # 发表信息
        pub_info = []
        if hasattr(paper.metadata, 'journal') and paper.metadata.journal:
            pub_info.append(paper.metadata.journal)
        if hasattr(paper.metadata, 'publication_date') and paper.metadata.publication_date:
            pub_info.append(paper.metadata.publication_date)
        elif hasattr(paper.metadata, 'date') and paper.metadata.date:
            pub_info.append(paper.metadata.date)
        elif hasattr(paper.metadata, 'year') and paper.metadata.year:
            pub_info.append(paper.metadata.year)

        if pub_info:
            md_parts.append(f"**发表信息:** {', '.join(pub_info)}\n")

        # DOI和URL
        if hasattr(paper.metadata, 'doi') and paper.metadata.doi:
            md_parts.append(f"**DOI:** {paper.metadata.doi}\n")
        if hasattr(paper.metadata, 'url') and paper.metadata.url:
            md_parts.append(f"**URL:** {paper.metadata.url}\n")

        # 摘要
        abstract_section = next((s for s in paper.sections if s.section_type == 'abstract'), None)
        if abstract_section:
            md_parts.append(f"## 摘要\n\n{abstract_section.content}\n")
        elif hasattr(paper.metadata, 'abstract') and paper.metadata.abstract:
            md_parts.append(f"## 摘要\n\n{paper.metadata.abstract}\n")

        # 关键词
        if paper.keywords:
            md_parts.append(f"**关键词:** {', '.join(paper.keywords)}\n")

        # 章节内容
        md_parts.append(self._format_sections_markdown(paper.sections))

        # 图表
        if paper.figures:
            md_parts.append("## 图\n")
            for fig in paper.figures:
                md_parts.append(f"### {fig.id}: {fig.caption}\n\n{fig.content}\n")

        if paper.tables:
            md_parts.append("## 表\n")
            for table in paper.tables:
                md_parts.append(f"### {table.id}: {table.caption}\n\n{table.content}\n")

        # 公式
        if paper.formulas:
            md_parts.append("## 公式\n")
            for formula in paper.formulas:
                # 使用代码块包装公式内容，而不是作为标题
                formatted_content = self._format_formula_content(formula.content)
                md_parts.append(f"**{formula.id}**\n\n```math\n{formatted_content}\n```\n")

        # 参考文献
        if paper.references:
            md_parts.append("## 参考文献\n")
            for ref in paper.references:
                md_parts.append(f"{ref.id} {ref.text}\n")

        return "\n".join(md_parts)