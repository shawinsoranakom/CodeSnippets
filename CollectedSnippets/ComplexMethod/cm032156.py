def _build_enhanced_document(self, paper: PaperMetadata, criteria: SearchCriteria) -> str:
        """构建增强的文档表示"""
        components = []

        # 基本信息
        title = getattr(paper, 'title', '')
        authors = ', '.join(getattr(paper, 'authors', []))
        abstract = getattr(paper, 'abstract', '')
        year = getattr(paper, 'year', '')
        venue = getattr(paper, 'venue', '')

        components.extend([
            f"Title: {title}",
            f"Authors: {authors}",
            f"Year: {year}",
            f"Venue: {venue}",
            f"Abstract: {abstract}"
        ])

        # 根据查询类型添加额外信息
        if criteria:
            if criteria.query_type == "review":
                # 对于综述类查询，强调论文的综述性质
                title_lower = (title or '').lower()
                abstract_lower = (abstract or '').lower()
                if any(keyword in title_lower or keyword in abstract_lower
                      for keyword in ['review', 'survey', 'overview']):
                    components.append("This is a review/survey paper")

            elif criteria.query_type == "latest":
                # 对于最新论文查询，强调时间信息
                if year and int(year) >= criteria.start_year:
                    components.append(f"This is a recent paper from {year}")

            elif criteria.query_type == "recommend":
                # 对于推荐类查询，添加主题相关性信息
                if criteria.main_topic:
                    title_lower = (title or '').lower()
                    abstract_lower = (abstract or '').lower()
                    topic_relevance = any(topic.lower() in title_lower or topic.lower() in abstract_lower
                                        for topic in [criteria.main_topic] + (criteria.sub_topics or []))
                    if topic_relevance:
                        components.append(f"This paper is directly related to {criteria.main_topic}")

        return '\n'.join(components)