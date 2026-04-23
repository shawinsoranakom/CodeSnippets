async def _search_semantic(self, params: Dict, limit_multiplier: int = 1, min_year: int = 2015) -> List:
        """使用Semantic Scholar专用参数搜索"""
        try:
            original_limit = params.get("limit", 20)
            params["limit"] = original_limit * limit_multiplier

            # 只使用基本的搜索参数
            papers = await self.semantic.search(
                query=params.get("query", ""),
                limit=params["limit"]
            )

            # 在内存中进行过滤
            if papers and min_year:
                papers = [p for p in papers if getattr(p, 'year', 0) and p.year >= min_year]

            return papers or []

        except Exception as e:
            print(f"Semantic Scholar搜索出错: {str(e)}")
            return []