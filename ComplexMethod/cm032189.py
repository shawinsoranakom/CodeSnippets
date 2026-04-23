async def _search_bilingual_code(self, english_query: str, chinese_query: str, language: str = None, per_page: int = 30) -> List[Dict]:
        """同时搜索中英文代码并合并结果"""
        try:
            # 搜索英文代码
            english_results = await self._search_code(
                query=english_query,
                language=language,
                per_page=per_page
            )

            # 搜索中文代码
            chinese_results = await self._search_code(
                query=chinese_query,
                language=language,
                per_page=per_page
            )

            # 合并结果，去除重复项
            merged_results = []
            seen_files = set()

            # 优先添加英文结果
            for item in english_results:
                # 使用文件URL作为唯一标识
                file_url = item.get('html_url', '')
                if file_url and file_url not in seen_files:
                    seen_files.add(file_url)
                    merged_results.append(item)

            # 添加中文结果（排除重复）
            for item in chinese_results:
                file_url = item.get('html_url', '')
                if file_url and file_url not in seen_files:
                    seen_files.add(file_url)
                    merged_results.append(item)

            # 对结果进行排序，优先显示匹配度高的结果
            # 由于无法直接获取匹配度，这里使用仓库的星标数作为替代指标
            merged_results.sort(key=lambda x: x.get('repository', {}).get('stargazers_count', 0), reverse=True)

            return merged_results[:per_page]  # 返回合并后的前per_page个结果
        except Exception as e:
            print(f"双语代码搜索出错: {str(e)}")
            return []