async def _search_bilingual_repositories(self, english_query: str, chinese_query: str, language: str = None, min_stars: int = 0,
                                sort: str = "stars", per_page: int = 30) -> List[Dict]:
        """同时搜索中英文仓库并合并结果"""
        try:
            # 搜索英文仓库
            english_results = await self._search_repositories(
                query=english_query,
                language=language,
                min_stars=min_stars,
                sort=sort,
                per_page=per_page
            )

            # 搜索中文仓库
            chinese_results = await self._search_repositories(
                query=chinese_query,
                language=language,
                min_stars=min_stars,
                sort=sort,
                per_page=per_page
            )

            # 合并结果，去除重复项
            merged_results = []
            seen_repos = set()

            # 优先添加英文结果
            for repo in english_results:
                repo_id = repo.get('id')
                if repo_id and repo_id not in seen_repos:
                    seen_repos.add(repo_id)
                    merged_results.append(repo)

            # 添加中文结果（排除重复）
            for repo in chinese_results:
                repo_id = repo.get('id')
                if repo_id and repo_id not in seen_repos:
                    seen_repos.add(repo_id)
                    merged_results.append(repo)

            # 按星标数重新排序
            merged_results.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)

            return merged_results[:per_page]  # 返回合并后的前per_page个结果
        except Exception as e:
            print(f"双语仓库搜索出错: {str(e)}")
            return []