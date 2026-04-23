def rank_papers(
        self,
        query: str,
        papers: List[PaperMetadata],
        search_criteria: SearchCriteria = None,
        top_k: int = 40,
        use_rerank: bool = False,
        pre_filter_ratio: float = 0.5,
        max_papers: int = 150
    ) -> List[PaperMetadata]:
        """对论文进行重排序"""
        initial_count = len(papers) if papers else 0
        stats = {'initial': initial_count}

        if not papers or not query:
            return []

        # 更新论文的期刊指标
        self._update_paper_metrics(papers)

        # 构建增强查询
        # enhanced_query = self._build_enhanced_query(query, search_criteria) if search_criteria else query
        enhanced_query = query
        # 首先过滤不满足年份要求的论文
        if search_criteria and search_criteria.start_year and search_criteria.end_year:
            before_year_filter = len(papers)
            filtered_papers = []
            start_year = int(search_criteria.start_year)
            end_year = int(search_criteria.end_year)

            for paper in papers:
                paper_year = self._get_year_as_int(paper)
                if paper_year == 0 or start_year <= paper_year <= end_year:
                    filtered_papers.append(paper)

            papers = filtered_papers
            stats['after_year_filter'] = len(papers)

        if not papers:  # 如果过滤后没有论文，直接返回空列表
            return []

        # 新增：对少量论文的快速处理
        SMALL_PAPER_THRESHOLD = 10  # 定义"少量"论文的阈值
        if len(papers) <= SMALL_PAPER_THRESHOLD:
            # 对于少量论文，直接根据查询类型进行简单排序
            if search_criteria:
                if search_criteria.query_type == "latest":
                    papers.sort(key=lambda x: getattr(x, 'year', 0) or 0, reverse=True)
                elif search_criteria.query_type == "recommend":
                    papers.sort(key=lambda x: getattr(x, 'citations', 0) or 0, reverse=True)
                elif search_criteria.query_type == "review":
                    papers.sort(key=lambda x:
                        1 if any(keyword in (getattr(x, 'title', '') or '').lower() or
                                keyword in (getattr(x, 'abstract', '') or '').lower()
                                for keyword in ['review', 'survey', 'overview'])
                        else 0,
                        reverse=True
                    )
            return papers[:top_k]

        # 1. 优先处理最新的论文
        if search_criteria and search_criteria.query_type == "latest":
            papers = sorted(papers, key=lambda x: self._get_year_as_int(x), reverse=True)

        # 2. 如果是综述类查询，优先处理可能的综述论文
        if search_criteria and search_criteria.query_type == "review":
            papers = sorted(papers, key=lambda x:
                1 if any(keyword in (getattr(x, 'title', '') or '').lower() or
                        keyword in (getattr(x, 'abstract', '') or '').lower()
                        for keyword in ['review', 'survey', 'overview'])
                else 0,
                reverse=True
            )

        # 3. 如果论文数量超过限制，采用分层采样而不是完全随机
        if len(papers) > max_papers:
            before_max_limit = len(papers)
            papers = self._select_papers_strategically(papers, search_criteria, max_papers)
            stats['after_max_limit'] = len(papers)

        try:
            paper_texts = []
            valid_papers = []  # 4. 跟踪有效论文

            for paper in papers:
                if paper is None:
                    continue
                # 5. 预先过滤明显不相关的论文
                if search_criteria and search_criteria.start_year:
                    if getattr(paper, 'year', 0) and self._get_year_as_int(paper.year) < search_criteria.start_year:
                        continue

                doc = self._build_enhanced_document(paper, search_criteria)
                paper_texts.append(doc)
                valid_papers.append(paper)  # 记录对应的论文

            stats['after_valid_check'] = len(valid_papers)

            if not paper_texts:
                return []

            # 使用LLM判断相关性
            relevance_results = self.ranker.batch_check_relevance(
                query=enhanced_query,  # 使用增强的查询
                paper_texts=paper_texts,
                show_progress=True
            )

            # 6. 优化相关论文的选择策略
            relevant_papers = []
            for paper, is_relevant in zip(valid_papers, relevance_results):
                if is_relevant:
                    relevant_papers.append(paper)

            stats['after_llm_filter'] = len(relevant_papers)

            # 打印统计信息
            print(f"论文筛选统计: 初始数量={stats['initial']}, " +
                  f"年份过滤后={stats.get('after_year_filter', stats['initial'])}, " +
                  f"数量限制后={stats.get('after_max_limit', stats.get('after_year_filter', stats['initial']))}, " +
                  f"有效性检查后={stats['after_valid_check']}, " +
                  f"LLM筛选后={stats['after_llm_filter']}")

            # 7. 改进回退策略
            if len(relevant_papers) < min(5, len(papers)):
                # 如果相关论文太少，返回按引用量排序的论文
                return sorted(
                    papers[:top_k],
                    key=lambda x: getattr(x, 'citations', 0) or 0,
                    reverse=True
                )

            # 8. 对最终结果进行排序
            if search_criteria:
                if search_criteria.query_type == "latest":
                    # 最新论文优先，但同年份按IF排序
                    relevant_papers.sort(key=lambda x: (
                        self._get_year_as_int(x),
                        getattr(x, 'if_factor', 0) or 0
                    ), reverse=True)
                elif search_criteria.query_type == "recommend":
                    # IF指数优先，其次是引用量
                    relevant_papers.sort(key=lambda x: (
                        getattr(x, 'if_factor', 0) or 0,
                        getattr(x, 'citations', 0) or 0
                    ), reverse=True)
                else:
                    # 默认按IF指数排序
                    relevant_papers.sort(key=lambda x: getattr(x, 'if_factor', 0) or 0, reverse=True)

            return relevant_papers[:top_k]

        except Exception as e:
            print(f"论文排序时出错: {str(e)}")
            # 9. 改进错误处理的回退策略
            try:
                return sorted(
                    papers[:top_k],
                    key=lambda x: getattr(x, 'citations', 0) or 0,
                    reverse=True
                )
            except:
                return papers[:top_k] if papers else []