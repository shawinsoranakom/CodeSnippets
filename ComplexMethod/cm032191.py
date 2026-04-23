async def _search_bilingual_topics(self, english_query: str, chinese_query: str, per_page: int = 30) -> List[Dict]:
        """同时搜索中英文主题并合并结果"""
        try:
            # 搜索英文主题
            english_results = await self._search_topics(
                query=english_query,
                per_page=per_page
            )

            # 搜索中文主题
            chinese_results = await self._search_topics(
                query=chinese_query,
                per_page=per_page
            )

            # 合并结果，去除重复项
            merged_results = []
            seen_topics = set()

            # 优先添加英文结果
            for topic in english_results:
                topic_name = topic.get('name')
                if topic_name and topic_name not in seen_topics:
                    seen_topics.add(topic_name)
                    merged_results.append(topic)

            # 添加中文结果（排除重复）
            for topic in chinese_results:
                topic_name = topic.get('name')
                if topic_name and topic_name not in seen_topics:
                    seen_topics.add(topic_name)
                    merged_results.append(topic)

            # 可以按流行度进行排序（如果有）
            if merged_results and 'featured' in merged_results[0]:
                merged_results.sort(key=lambda x: x.get('featured', False), reverse=True)

            return merged_results[:per_page]  # 返回合并后的前per_page个结果
        except Exception as e:
            print(f"双语主题搜索出错: {str(e)}")
            return []