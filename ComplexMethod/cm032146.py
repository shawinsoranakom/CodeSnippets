async def search(
        self,
        query: str,
        limit: int = 10,
        sort_by: str = None,
        sort_order: str = None,
        start_year: int = None
    ) -> List[Dict]:
        """搜索论文"""
        try:
            # 使用默认排序如果提供的排序选项无效
            if not sort_by or sort_by not in self.sort_options:
                sort_by = self.default_sort

            # 使用默认排序顺序如果提供的顺序无效
            if not sort_order or sort_order not in self.sort_order_options:
                sort_order = self.default_order

            # 如果指定了起始年份，添加到查询中
            if start_year:
                query = f"{query} AND submittedDate:[{start_year}0101 TO 99991231]"

            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=self.sort_options[sort_by],
                sort_order=self.sort_order_options[sort_order]
            )

            results = list(self.client.results(search))
            return [self._parse_paper_data(result) for result in results]
        except Exception as e:
            print(f"搜索论文时发生错误: {str(e)}")
            return []