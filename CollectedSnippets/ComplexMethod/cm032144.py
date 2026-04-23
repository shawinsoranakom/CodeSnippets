async def example_usage():
    """SemanticScholarSource使用示例"""
    semantic = SemanticScholarSource()

    try:
        # 示例1：使用DOI直接获取论文
        print("\n=== 示例1：通过DOI获取论文 ===")
        doi = "10.18653/v1/N19-1423"  # BERT论文
        print(f"获取DOI为 {doi} 的论文信息...")

        paper = await semantic.get_paper_details(doi)
        if paper:
            print("\n--- 论文信息 ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            print(f"URL: {paper.url}")
            if paper.abstract:
                print(f"\n摘要:")
                print(paper.abstract)
            print(f"\n引用次数: {paper.citations}")
            print(f"发表venue: {paper.venue}")

        # 示例2：搜索论文
        print("\n=== 示例2：搜索论文 ===")
        query = "BERT pre-training"
        print(f"搜索关键词 '{query}' 相关的论文...")
        papers = await semantic.search(query=query, limit=3)

        for i, paper in enumerate(papers, 1):
            print(f"\n--- 搜索结果 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            if paper.abstract:
                print(f"\n摘要:")
                print(paper.abstract)
            print(f"\nDOI: {paper.doi}")
            print(f"引用次数: {paper.citations}")

        # 示例3：获取论文推荐
        print("\n=== 示例3：获取论文推荐 ===")
        print(f"获取与论文 {doi} 相关的推荐论文...")
        recommendations = await semantic.get_recommended_papers(doi, limit=3)
        for i, paper in enumerate(recommendations, 1):
            print(f"\n--- 推荐论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")

        # 示例4：基于多篇论文的推荐
        print("\n=== 示例4：基于多篇论文的推荐 ===")
        positive_dois = ["10.18653/v1/N19-1423", "10.18653/v1/P19-1285"]
        print(f"基于 {len(positive_dois)} 篇论文获取推荐...")
        multi_recommendations = await semantic.get_recommended_papers_from_lists(
            positive_dois=positive_dois,
            limit=3
        )
        for i, paper in enumerate(multi_recommendations, 1):
            print(f"\n--- 推荐论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")

        # 示例5：搜索作者
        print("\n=== 示例5：搜索作者 ===")
        author_query = "Yann LeCun"
        print(f"搜索作者: '{author_query}'")
        authors = await semantic.search_author(author_query, limit=3)
        for i, author in enumerate(authors, 1):
            print(f"\n--- 作者 {i} ---")
            print(f"姓名: {author['name']}")
            print(f"论文数量: {author['paper_count']}")
            print(f"总引用次数: {author['citation_count']}")

        # 示例6：获取作者详情
        print("\n=== 示例6：获取作者详情 ===")
        if authors:  # 使用第一个搜索结果的作者ID
            author_id = authors[0]['author_id']
            print(f"获取作者ID {author_id} 的详细信息...")
            author_details = await semantic.get_author_details(author_id)
            if author_details:
                print(f"姓名: {author_details['name']}")
                print(f"H指数: {author_details['h_index']}")
                print(f"总引用次数: {author_details['citation_count']}")
                print(f"发表论文数: {author_details['paper_count']}")

        # 示例7：获取作者论文
        print("\n=== 示例7：获取作者论文 ===")
        if authors:  # 使用第一个搜索结果的作者ID
            author_id = authors[0]['author_id']
            print(f"获取作者 {authors[0]['name']} 的论文列表...")
            author_papers = await semantic.get_author_papers(author_id, limit=3)
            for i, paper in enumerate(author_papers, 1):
                print(f"\n--- 论文 {i} ---")
                print(f"标题: {paper.title}")
                print(f"发表年份: {paper.year}")
                print(f"引用次数: {paper.citations}")

        # 示例8：论文标题自动补全
        print("\n=== 示例8：论文标题自动补全 ===")
        title_query = "Attention is all"
        print(f"搜索标题: '{title_query}'")
        suggestions = await semantic.get_paper_autocomplete(title_query)
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"\n--- 建议 {i} ---")
            print(f"标题: {suggestion['title']}")
            print(f"发表年份: {suggestion['year']}")
            print(f"发表venue: {suggestion['venue']}")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())