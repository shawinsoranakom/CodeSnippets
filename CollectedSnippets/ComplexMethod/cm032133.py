async def search(
        self,
        query: str,
        limit: int = 100,
        sort_by: str = "relevance",
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
            # 添加年份过滤
            if start_year:
                query = f"{query} AND {start_year}:3000[dp]"

            # 构建搜索URL
            search_url = (
                f"{self.base_url}/esearch.fcgi?"
                f"db=pubmed&term={quote(query)}&retmax={limit}"
                f"&usehistory=y&api_key={self.api_key}"
            )

            if sort_by == "date":
                search_url += "&sort=date"

            # 获取搜索结果
            response = await self._make_request(search_url)
            if not response:
                return []

            # 解析XML响应
            root = ET.fromstring(response)
            id_list = root.findall(".//Id")
            pmids = [id_elem.text for id_elem in id_list]

            if not pmids:
                return []

            # 批量获取论文详情
            papers = []
            batch_size = 50
            for i in range(0, len(pmids), batch_size):
                batch = pmids[i:i + batch_size]
                batch_papers = await self._fetch_papers_batch(batch)
                papers.extend(batch_papers)

            return papers

        except Exception as e:
            print(f"搜索论文时发生错误: {str(e)}")
            return []