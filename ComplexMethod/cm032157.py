def _select_papers_strategically(
        self,
        papers: List[PaperMetadata],
        search_criteria: SearchCriteria,
        max_papers: int = 150
    ) -> List[PaperMetadata]:
        """战略性地选择论文子集，优先选择非Crossref来源的论文，
        当ADS论文充足时排除arXiv论文"""
        if len(papers) <= max_papers:
            return papers

        # 1. 首先按来源分组
        papers_by_source = {
            'crossref': [],
            'adsabs': [],
            'arxiv': [],
            'others': []  # semantic, pubmed等其他来源
        }

        for paper in papers:
            source = getattr(paper, 'source', '')
            if source == 'crossref':
                papers_by_source['crossref'].append(paper)
            elif source == 'adsabs':
                papers_by_source['adsabs'].append(paper)
            elif source == 'arxiv':
                papers_by_source['arxiv'].append(paper)
            else:
                papers_by_source['others'].append(paper)

        # 2. 计算分数的通用函数
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

        result = []

        # 3. 处理ADS和arXiv论文
        non_crossref_papers = papers_by_source['others']  # 首先添加其他来源的论文

        # 添加ADS论文
        if papers_by_source['adsabs']:
            non_crossref_papers.extend(papers_by_source['adsabs'])

        # 只有当ADS论文不足20篇时，才添加arXiv论文
        if len(papers_by_source['adsabs']) <= 20:
            non_crossref_papers.extend(papers_by_source['arxiv'])
        elif not papers_by_source['adsabs'] and papers_by_source['arxiv']:
            # 如果没有ADS论文但有arXiv论文，也使用arXiv论文
            non_crossref_papers.extend(papers_by_source['arxiv'])

        # 4. 对非Crossref论文评分和排序
        scored_non_crossref = [(p, calculate_paper_score(p)) for p in non_crossref_papers]
        scored_non_crossref.sort(key=lambda x: x[1], reverse=True)

        # 5. 先添加高分的非Crossref论文
        non_crossref_limit = max_papers * 0.9  # 90%的配额给非Crossref论文
        if len(scored_non_crossref) >= non_crossref_limit:
            result.extend([p[0] for p in scored_non_crossref[:int(non_crossref_limit)]])
        else:
            result.extend([p[0] for p in scored_non_crossref])

        # 6. 如果还有剩余空间，考虑添加Crossref论文
        remaining_slots = max_papers - len(result)
        if remaining_slots > 0 and papers_by_source['crossref']:
            # 计算Crossref论文的最大数量（不超过总数的10%）
            max_crossref = min(remaining_slots, max_papers * 0.1)

            # 对Crossref论文评分和排序
            scored_crossref = [(p, calculate_paper_score(p)) for p in papers_by_source['crossref']]
            scored_crossref.sort(key=lambda x: x[1], reverse=True)

            # 添加最高分的Crossref论文
            result.extend([p[0] for p in scored_crossref[:int(max_crossref)]])

        # 7. 如果使用了Crossref论文后还有空位，继续使用非Crossref论文填充
        if len(result) < max_papers and len(scored_non_crossref) > len(result):
            remaining_non_crossref = [p[0] for p in scored_non_crossref[len(result):]]
            result.extend(remaining_non_crossref[:max_papers - len(result)])

        return result