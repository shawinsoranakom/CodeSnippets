async def _search_bilingual_users(self, english_query: str, chinese_query: str, per_page: int = 30) -> List[Dict]:
        """同时搜索中英文用户并合并结果"""
        try:
            # 搜索英文用户
            english_results = await self._search_users(
                query=english_query,
                per_page=per_page
            )

            # 搜索中文用户
            chinese_results = await self._search_users(
                query=chinese_query,
                per_page=per_page
            )

            # 合并结果，去除重复项
            merged_results = []
            seen_users = set()

            # 优先添加英文结果
            for user in english_results:
                user_id = user.get('id')
                if user_id and user_id not in seen_users:
                    seen_users.add(user_id)
                    merged_results.append(user)

            # 添加中文结果（排除重复）
            for user in chinese_results:
                user_id = user.get('id')
                if user_id and user_id not in seen_users:
                    seen_users.add(user_id)
                    merged_results.append(user)

            # 按关注者数量进行排序
            merged_results.sort(key=lambda x: x.get('followers', 0), reverse=True)

            return merged_results[:per_page]  # 返回合并后的前per_page个结果
        except Exception as e:
            print(f"双语用户搜索出错: {str(e)}")
            return []