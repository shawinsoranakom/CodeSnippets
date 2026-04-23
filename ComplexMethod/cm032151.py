async def search(
        self,
        query: str,
        limit: int = 100,
        sort_by: str = None,
        sort_order: str = None,
        start_year: int = None
    ) -> List[PaperMetadata]:
        """搜索论文

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
            sort_by: 排序字段
            sort_order: 排序顺序
            start_year: 起始年份
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # 请求更多的结果以补偿可能被过滤掉的文章
            adjusted_limit = min(limit * 3, 1000)  # 设置上限以避免请求过多
            params = {
                "query": query,
                "rows": adjusted_limit,
                "select": (
                    "DOI,title,author,published-print,abstract,reference,"
                    "container-title,is-referenced-by-count,type,"
                    "publisher,ISSN,ISBN,issue,volume,page"
                )
            }

            # 添加年份过滤
            if start_year:
                params["filter"] = f"from-pub-date:{start_year}"

            # 添加排序
            if sort_by:
                params["sort"] = sort_by
                if sort_order:
                    params["order"] = sort_order

            async with session.get(
                f"{self.base_url}/works",
                params=params
            ) as response:
                if response.status != 200:
                    print(f"API请求失败: HTTP {response.status}")
                    print(f"响应内容: {await response.text()}")
                    return []

                data = await response.json()
                items = data.get("message", {}).get("items", [])
                if not items:
                    print(f"未找到相关论文")
                    return []

                # 过滤掉没有摘要的文章
                papers = []
                filtered_count = 0
                for work in items:
                    paper = self._parse_work(work)
                    if paper.abstract and paper.abstract.strip():
                        papers.append(paper)
                        if len(papers) >= limit:  # 达到原始请求的限制后停止
                            break
                    else:
                        filtered_count += 1

                print(f"找到 {len(items)} 篇相关论文，其中 {filtered_count} 篇因缺少摘要被过滤")
                print(f"返回 {len(papers)} 篇包含摘要的论文")
                return papers