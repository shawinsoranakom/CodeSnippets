async def example_usage():
    """PubMedSource使用示例"""
    pubmed = PubMedSource()

    try:
        # 示例1：基本搜索
        print("\n=== 示例1：搜索COVID-19相关论文 ===")
        papers = await pubmed.search("COVID-19", limit=3)
        for i, paper in enumerate(papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            if paper.abstract:
                print(f"摘要: {paper.abstract[:200]}...")

        # 示例2：获取论文详情
        if papers:
            print("\n=== 示例2：获取论文详情 ===")
            paper_id = papers[0].url.split("/")[-2]
            paper = await pubmed.get_paper_details(paper_id)
            if paper:
                print(f"标题: {paper.title}")
                print(f"期刊: {paper.venue}")
                print(f"机构: {', '.join(paper.institutions)}")

        # 示例3：获取相关论文
        if papers:
            print("\n=== 示例3：获取相关论文 ===")
            related = await pubmed.get_related_papers(paper_id, limit=3)
            for i, paper in enumerate(related, 1):
                print(f"\n--- 相关论文 {i} ---")
                print(f"标题: {paper.title}")
                print(f"作者: {', '.join(paper.authors)}")

        # 示例4：按作者搜索
        print("\n=== 示例4：按作者搜索 ===")
        author_papers = await pubmed.search_by_author("Fauci AS", limit=3)
        for i, paper in enumerate(author_papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"发表年份: {paper.year}")

        # 示例5：按期刊搜索
        print("\n=== 示例5：按期刊搜索 ===")
        journal_papers = await pubmed.search_by_journal("Nature", limit=3)
        for i, paper in enumerate(journal_papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"发表年份: {paper.year}")

        # 示例6：获取最新论文
        print("\n=== 示例6：获取最新论文 ===")
        latest = await pubmed.get_latest_papers(days=7, limit=3)
        for i, paper in enumerate(latest, 1):
            print(f"\n--- 最新论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"发表日期: {paper.venue_info.get('pub_date')}")

        # 示例7：获取论文的参考文献
        if papers:
            print("\n=== 示例7：获取论文的参考文献 ===")
            paper_id = papers[0].url.split("/")[-2]
            references = await pubmed.get_references(paper_id)
            for i, paper in enumerate(references[:3], 1):
                print(f"\n--- 参考文献 {i} ---")
                print(f"标题: {paper.title}")
                print(f"作者: {', '.join(paper.authors)}")
                print(f"发表年份: {paper.year}")

        # 示例8：尝试获取引用信息（将返回空列表）
        if papers:
            print("\n=== 示例8：获取论文的引用信息 ===")
            paper_id = papers[0].url.split("/")[-2]
            citations = await pubmed.get_citations(paper_id)
            print(f"引用数据：{len(citations)} (PubMed API不提供引用信息)")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())