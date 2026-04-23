async def _get_paper_details(self, criteria: SearchCriteria):
        """获取论文详情"""
        try:
            if criteria.paper_source == "arxiv":
                # 使用 arxiv ID 搜索
                papers = await self.arxiv.search_by_id(criteria.paper_id)
                return papers[0] if papers else None

            elif criteria.paper_source == "doi":
                # 尝试从所有来源获取
                paper = await self.semantic.get_paper_by_doi(criteria.paper_id)
                if not paper:
                    # 如果Semantic Scholar没有找到，尝试PubMed
                    papers = await self.pubmed.search(
                        f"{criteria.paper_id}[doi]",
                        limit=1
                    )
                    if papers:
                        return papers[0]
                return paper

            elif criteria.paper_source == "title":
                # 使用_search_all_sources搜索
                search_params = {
                    'max_papers': 1,
                    'min_year': 1900,  # 不限制年份
                    'search_multiplier': 1
                }

                # 设置搜索参数
                criteria.arxiv_params = {
                    "search_type": "basic",
                    "query": f'ti:"{criteria.paper_title}"',
                    "limit": 1
                }
                criteria.semantic_params = {
                    "query": criteria.paper_title,
                    "limit": 1
                }
                criteria.pubmed_params = {
                    "search_type": "basic",
                    "query": f'"{criteria.paper_title}"[Title]',
                    "limit": 1
                }

                papers = await self._search_all_sources(criteria, search_params)
                return papers[0] if papers else None

            # 如果都没有找到，尝试使用 main_topic 作为标题搜索
            if not criteria.paper_title and not criteria.paper_id:
                search_params = {
                    'max_papers': 1,
                    'min_year': 1900,
                    'search_multiplier': 1
                }

                # 设置搜索参数
                criteria.arxiv_params = {
                    "search_type": "basic",
                    "query": f'ti:"{criteria.main_topic}"',
                    "limit": 1
                }
                criteria.semantic_params = {
                    "query": criteria.main_topic,
                    "limit": 1
                }
                criteria.pubmed_params = {
                    "search_type": "basic",
                    "query": f'"{criteria.main_topic}"[Title]',
                    "limit": 1
                }

                papers = await self._search_all_sources(criteria, search_params)
                return papers[0] if papers else None

            return None

        except Exception as e:
            print(f"获取论文详情时出错: {str(e)}")
            return None