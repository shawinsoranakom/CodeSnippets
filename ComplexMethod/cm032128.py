async def _get_recommendations(self, seed_papers: List, multiplier: int = 1) -> List:
        """获取推荐论文"""
        recommendations = []
        base_limit = 3 * multiplier

        # 将种子论文添加到推荐列表中
        recommendations.extend(seed_papers)

        # 只使用前5篇论文作为种子
        seed_papers = seed_papers[:5]

        for paper in seed_papers:
            try:
                if paper.doi and paper.doi.startswith("10.48550/arXiv."):
                    # arXiv论文
                    arxiv_id = paper.doi.split(".")[-1]
                    paper_details = await self.arxiv.get_paper_details(arxiv_id)
                    if paper_details and hasattr(paper_details, 'venue'):
                        category = paper_details.venue.split(":")[-1]
                        similar_papers = await self.arxiv.search_by_category(
                            category,
                            limit=base_limit,
                            sort_by='relevance'
                        )
                        recommendations.extend(similar_papers)
                elif paper.doi:  # 只对有DOI的论文获取推荐
                    # Semantic Scholar论文
                    similar_papers = await self.semantic.get_recommended_papers(
                        paper.doi,
                        limit=base_limit
                    )
                    if similar_papers:  # 只添加成功获取的推荐
                        recommendations.extend(similar_papers)
                else:
                    # 对于没有DOI的论文，使用标题进行相关搜索
                    if paper.title:
                        similar_papers = await self.semantic.search(
                            query=paper.title,
                            limit=base_limit
                        )
                        recommendations.extend(similar_papers)

            except Exception as e:
                print(f"获取论文 '{paper.title}' 的推荐时发生错误: {str(e)}")
                continue

        # 去重处理
        seen_dois = set()
        unique_recommendations = []
        for paper in recommendations:
            if paper.doi and paper.doi not in seen_dois:
                seen_dois.add(paper.doi)
                unique_recommendations.append(paper)
            elif not paper.doi and paper not in unique_recommendations:
                unique_recommendations.append(paper)

        return unique_recommendations