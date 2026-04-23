async def search(
        self,
        query: str,
        limit: int = 100,
        sort_by: str = "relevance",
        start_year: int = None
    ) -> List[PaperMetadata]:
        """搜索论文"""
        try:
            params = {
                "query": query,
                "count": min(limit, 100),
                "view": "STANDARD",
                # 移除dc:description字段，因为它在STANDARD视图中不可用
                "field": "dc:title,dc:creator,prism:doi,prism:coverDate,citedby-count,prism:publicationName"
            }

            # 添加年份过滤
            if start_year:
                params["date"] = f"{start_year}-present"

            # 添加排序
            if sort_by == "date":
                params["sort"] = "-coverDate"
            elif sort_by == "cited":
                params["sort"] = "-citedby-count"

            # 发送搜索请求
            response = await self._make_request(
                f"{self.base_url}/search/scopus",
                params=params
            )

            if not response or "search-results" not in response:
                return []

            # 解析搜索结果
            entries = response["search-results"].get("entry", [])
            papers = [paper for paper in (self._parse_entry(entry) for entry in entries) if paper is not None]

            # 尝试为每篇论文获取摘要
            for paper in papers:
                if paper.doi:
                    paper.abstract = await self.fetch_abstract(paper.doi) or ""

            return papers

        except Exception as e:
            print(f"搜索论文时发生错误: {str(e)}")
            return []