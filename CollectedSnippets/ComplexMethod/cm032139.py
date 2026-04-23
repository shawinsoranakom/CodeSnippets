async def search(
        self,
        query: str,
        limit: int = 100,
        sort_by: str = None,
        start_year: int = None
    ) -> List[PaperMetadata]:
        """搜索论文

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
            sort_by: 排序方式 ('relevance', 'date', 'citations')
            start_year: 起始年份

        Returns:
            论文列表
        """
        try:
            # 构建查询参数
            params = {
                "query": query,
                "count": min(limit, 100),  # Scopus API单次请求限制
                "start": 0
            }

            # 添加年份过滤
            if start_year:
                params["date"] = f"{start_year}-present"

            # 添加排序
            if sort_by:
                sort_map = {
                    "relevance": "-score",
                    "date": "-coverDate",
                    "citations": "-citedby-count"
                }
                if sort_by in sort_map:
                    params["sort"] = sort_map[sort_by]

            # 发送请求
            url = f"{self.base_url}/search/scopus"
            response = await self._make_request(url, params)

            if not response or "search-results" not in response:
                return []

            # 解析结果
            results = response["search-results"].get("entry", [])
            papers = []

            for result in results:
                paper = self._parse_paper_data(result)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            print(f"搜索论文时发生错误: {str(e)}")
            return []