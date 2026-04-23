def _build_enhanced_query(self, query: str, criteria: SearchCriteria) -> str:
        """构建增强的查询文本"""
        components = []

        # 强调这是用户的原始查询，是最重要的匹配依据
        components.append(f"Original user query that must be primarily matched: {query}")

        if criteria:
            # 添加主题（如果与原始查询不同）
            if criteria.main_topic and criteria.main_topic != query:
                components.append(f"Additional context - The main topic is about: {criteria.main_topic}")

            # 添加子主题
            if criteria.sub_topics:
                components.append(f"Secondary aspects to consider: {', '.join(criteria.sub_topics)}")

            # 添加查询类型相关信息
            if criteria.query_type == "review":
                components.append("Paper type preference: Looking for comprehensive review papers, survey papers, or overview papers")
            elif criteria.query_type == "latest":
                components.append("Temporal preference: Focus on the most recent developments and latest papers")
            elif criteria.query_type == "recommend":
                components.append("Impact preference: Consider influential and fundamental papers")

        # 直接连接所有组件，保持语序
        enhanced_query = ' '.join(components)

        # 限制长度但不打乱顺序
        if len(enhanced_query) > 1000:
            enhanced_query = enhanced_query[:997] + "..."

        return enhanced_query