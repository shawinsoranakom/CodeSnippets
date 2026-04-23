async def example_usage():
    """ScopusSource使用示例"""
    scopus = ScopusSource()

    try:
        # 示例1：基本搜索
        print("\n=== 示例1：搜索机器学习相关论文 ===")
        papers = await scopus.search("machine learning", limit=3)
        print(f"\n找到 {len(papers)} 篇相关论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"发表期刊: {paper.venue}")
            print(f"引用次数: {paper.citations}")
            print(f"DOI: {paper.doi}")
            if paper.abstract:
                print(f"摘要:\n{paper.abstract}")
            print("-" * 80)

        # 示例2：按作者搜索
        print("\n=== 示例2：搜索特定作者的论文 ===")
        author_papers = await scopus.search_by_author("Hinton G.", limit=3)
        print(f"\n找到 {len(author_papers)} 篇 Hinton 的论文:")
        for i, paper in enumerate(author_papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"发表期刊: {paper.venue}")
            print(f"引用次数: {paper.citations}")
            print(f"DOI: {paper.doi}")
            if paper.abstract:
                print(f"摘要:\n{paper.abstract}")
            print("-" * 80)

        # 示例3：根据关键词搜索相关论文
        print("\n=== 示例3：搜索人工智能相关论文 ===")
        keywords = "artificial intelligence AND deep learning"
        papers = await scopus.search(
            query=keywords,
            limit=5,
            sort_by="citations",  # 按引用次数排序
            start_year=2020  # 只搜索2020年之后的论文
        )

        print(f"\n找到 {len(papers)} 篇相关论文:")
        for i, paper in enumerate(papers, 1):
            print(f"\n论文 {i}:")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"发表期刊: {paper.venue}")
            print(f"引用次数: {paper.citations}")
            print(f"DOI: {paper.doi}")
            if paper.abstract:
                print(f"摘要:\n{paper.abstract}")
            print("-" * 80)

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())