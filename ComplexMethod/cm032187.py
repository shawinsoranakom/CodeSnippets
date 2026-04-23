async def _search_repositories(self, query: str, language: str = None, min_stars: int = 0,
                                sort: str = "stars", per_page: int = 30) -> List[Dict]:
        """搜索仓库"""
        try:
            # 构建查询字符串
            if min_stars > 0 and "stars:>" not in query:
                query += f" stars:>{min_stars}"

            if language and "language:" not in query:
                query += f" language:{language}"

            # 执行搜索
            result = await self.github.search_repositories(
                query=query,
                sort=sort,
                per_page=per_page
            )

            if result and "items" in result:
                return result["items"]
            return []
        except Exception as e:
            print(f"仓库搜索出错: {str(e)}")
            return []