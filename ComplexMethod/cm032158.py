def calculate_paper_score(paper):
            score = 0
            title = (getattr(paper, 'title', '') or '').lower()
            abstract = (getattr(paper, 'abstract', '') or '').lower()
            year = self._get_year_as_int(paper)
            citations = getattr(paper, 'citations', 0) or 0

            # 安全地获取搜索条件
            main_topic = (getattr(search_criteria, 'main_topic', '') or '').lower()
            sub_topics = getattr(search_criteria, 'sub_topics', []) or []
            query_type = getattr(search_criteria, 'query_type', '')
            start_year = getattr(search_criteria, 'start_year', 0) or 0

            # 主题相关性得分
            if main_topic and main_topic in title:
                score += 10
            if main_topic and main_topic in abstract:
                score += 5

            # 子主题相关性得分
            for sub_topic in sub_topics:
                if sub_topic and sub_topic.lower() in title:
                    score += 5
                if sub_topic and sub_topic.lower() in abstract:
                    score += 2.5

            # 根据查询类型调整分数
            if query_type == "review":
                review_keywords = ['review', 'survey', 'overview']
                if any(keyword in title for keyword in review_keywords):
                    score *= 1.5
                if any(keyword in abstract for keyword in review_keywords):
                    score *= 1.2
            elif query_type == "latest":
                if year and start_year:
                    year_int = year if isinstance(year, int) else self._get_year_as_int(paper)
                    start_year_int = start_year if isinstance(start_year, int) else int(start_year)
                    if year_int >= start_year_int:
                        recency_bonus = min(5, (year_int - start_year_int))
                        score += recency_bonus * 2
            elif query_type == "recommend":
                citation_score = min(10, citations / 100)
                score += citation_score

            return score