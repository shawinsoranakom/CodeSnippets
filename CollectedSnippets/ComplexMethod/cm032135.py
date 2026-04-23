async def example_usage():
    """ElsevierSource使用示例"""
    elsevier = ElsevierSource()

    try:
        # 首先测试API访问权限
        print("\n=== 测试API访问权限 ===")
        await elsevier.test_api_access()

        # 示例1：基本搜索
        print("\n=== 示例1：搜索机器学习相关论文 ===")
        papers = await elsevier.search("machine learning", limit=3)
        for i, paper in enumerate(papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            print(f"URL: {paper.url}")
            print(f"引用次数: {paper.citations}")
            print(f"期刊/会议: {paper.venue}")
            print("期刊信息:")
            for key, value in paper.venue_info.items():
                if value:  # 只打印非空值
                    print(f"  - {key}: {value}")

        # 示例2：获取引用信息
        if papers and papers[0].doi:
            print("\n=== 示例2：获取引用该论文的文献 ===")
            citations = await elsevier.get_citations(papers[0].doi, limit=3)
            for i, paper in enumerate(citations, 1):
                print(f"\n--- 引用论文 {i} ---")
                print(f"标题: {paper.title}")
                print(f"作者: {', '.join(paper.authors)}")
                print(f"发表年份: {paper.year}")
                print(f"DOI: {paper.doi}")
                print(f"引用次数: {paper.citations}")
                print(f"期刊/会议: {paper.venue}")

        # 示例3：获取参考文献
        if papers and papers[0].doi:
            print("\n=== 示例3：获取论文的参考文献 ===")
            references = await elsevier.get_references(papers[0].doi)
            for i, paper in enumerate(references[:3], 1):
                print(f"\n--- 参考文献 {i} ---")
                print(f"标题: {paper.title}")
                print(f"作者: {', '.join(paper.authors)}")
                print(f"发表年份: {paper.year}")
                print(f"DOI: {paper.doi}")
                print(f"期刊/会议: {paper.venue}")

        # 示例4：按作者搜索
        print("\n=== 示例4：按作者搜索 ===")
        author_papers = await elsevier.search_by_author("Hinton G", limit=3)
        for i, paper in enumerate(author_papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            print(f"引用次数: {paper.citations}")
            print(f"期刊/会议: {paper.venue}")

        # 示例5：按机构搜索
        print("\n=== 示例5：按机构搜索 ===")
        affiliation_papers = await elsevier.search_by_affiliation("60027950", limit=3)  # MIT的机构ID
        for i, paper in enumerate(affiliation_papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            print(f"引用次数: {paper.citations}")
            print(f"期刊/会议: {paper.venue}")

        # 示例6：获取论文摘要
        print("\n=== 示例6：获取论文摘要 ===")
        test_doi = "10.1016/j.artint.2021.103535"
        abstract = await elsevier.fetch_abstract(test_doi)
        if abstract:
            print(f"摘要: {abstract[:200]}...")  # 只显示前200个字符
        else:
            print("无法获取摘要")

        # 在搜索结果中显示摘要
        print("\n=== 示例7：搜索结果中的摘要 ===")
        papers = await elsevier.search("machine learning", limit=1)
        for paper in papers:
            print(f"标题: {paper.title}")
            print(f"摘要: {paper.abstract[:200]}..." if paper.abstract else "摘要: 无")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())