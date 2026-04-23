async def _search_all_sources(self, criteria: SearchCriteria, search_params: Dict) -> List:
        """从所有数据源搜索论文"""
        search_tasks = []

        # # 检查是否需要执行PubMed搜索
        # is_using_pubmed = criteria.pubmed_params.get("search_type") != "none" and criteria.pubmed_params.get("query") != "none"
        is_using_pubmed = False # 开源版本不再搜索pubmed

        # 如果使用PubMed，则只执行PubMed和Semantic Scholar搜索
        if is_using_pubmed:
            search_tasks.append(
                self._search_pubmed(
                    criteria.pubmed_params,
                    limit_multiplier=search_params['search_multiplier'],
                    min_year=criteria.start_year
                )
            )

            # Semantic Scholar总是执行搜索
            search_tasks.append(
                self._search_semantic(
                    criteria.semantic_params,
                    limit_multiplier=search_params['search_multiplier'],
                    min_year=criteria.start_year
                )
            )
        else:

            # 如果不使用ADS，则执行Crossref搜索
            if criteria.crossref_params.get("search_type") != "none" and criteria.crossref_params.get("query") != "none":
                search_tasks.append(
                    self._search_crossref(
                        criteria.crossref_params,
                        limit_multiplier=search_params['search_multiplier'],
                        min_year=criteria.start_year
                    )
                )

            search_tasks.append(
                self._search_arxiv(
                    criteria.arxiv_params,
                    limit_multiplier=search_params['search_multiplier'],
                    min_year=criteria.start_year
                )
            )
            if get_conf("SEMANTIC_SCHOLAR_KEY"):
                search_tasks.append(
                    self._search_semantic(
                        criteria.semantic_params,
                        limit_multiplier=search_params['search_multiplier'],
                        min_year=criteria.start_year
                    )
                )

        # 执行所有需要的搜索任务
        papers = await asyncio.gather(*search_tasks)

        # 合并所有来源的论文并统计各来源的数量
        all_papers = []
        source_counts = {
            'arxiv': 0,
            'semantic': 0,
            'pubmed': 0,
            'crossref': 0,
            'adsabs': 0
        }

        for source_papers in papers:
            if source_papers:
                for paper in source_papers:
                    source = getattr(paper, 'source', 'unknown')
                    if source in source_counts:
                        source_counts[source] += 1
                all_papers.extend(source_papers)

        # 打印各来源的论文数量
        print("\n=== 各数据源找到的论文数量 ===")
        for source, count in source_counts.items():
            if count > 0:  # 只打印有论文的来源
                print(f"{source.capitalize()}: {count} 篇")
        print(f"总计: {len(all_papers)} 篇")
        print("===========================\n")

        return all_papers