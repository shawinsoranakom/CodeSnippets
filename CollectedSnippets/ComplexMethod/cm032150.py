async def example_usage():
    """CrossrefSource使用示例"""
    crossref = CrossrefSource(api_key=None)

    try:
        # 示例1：基本搜索，使用不同的排序方式
        print("\n=== 示例1：搜索最新的机器学习论文 ===")
        papers = await crossref.search(
            query="machine learning",
            limit=3,
            sort_by="published",
            sort_order="desc",
            start_year=2023
        )

        for i, paper in enumerate(papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            print(f"URL: {paper.url}")
            if paper.abstract:
                print(f"摘要: {paper.abstract[:200]}...")
            if paper.institutions:
                print(f"机构: {', '.join(paper.institutions)}")
            print(f"引用次数: {paper.citations}")
            print(f"发表venue: {paper.venue}")
            print(f"venue类型: {paper.venue_type}")
            if paper.venue_info:
                print("Venue详细信息:")
                for key, value in paper.venue_info.items():
                    if value:
                        print(f"  - {key}: {value}")

        # 示例2：按DOI获取论文详情
        print("\n=== 示例2：获取特定论文详情 ===")
        # 使用BERT论文的DOI
        doi = "10.18653/v1/N19-1423"
        paper = await crossref.get_paper_details(doi)
        if paper:
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            if paper.abstract:
                print(f"摘要: {paper.abstract[:200]}...")
            print(f"引用次数: {paper.citations}")

        # 示例3：按作者搜索
        print("\n=== 示例3：搜索特定作者的论文 ===")
        author_papers = await crossref.search_by_authors(
            authors=["Yoshua Bengio"],
            limit=3,
            sort_by="published",
            start_year=2020
        )
        for i, paper in enumerate(author_papers, 1):
            print(f"\n--- {i}. {paper.title} ---")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")
            print(f"引用次数: {paper.citations}")

        # 示例4：按日期范围搜索
        print("\n=== 示例4：搜索特定日期范围的论文 ===")
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 最近一个月
        recent_papers = await crossref.search_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=3,
            sort_by="published",
            sort_order="desc"
        )
        for i, paper in enumerate(recent_papers, 1):
            print(f"\n--- 最近发表的论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors)}")
            print(f"发表年份: {paper.year}")
            print(f"DOI: {paper.doi}")

        # 示例5：获取论文引用信息
        print("\n=== 示例5：获取论文引用信息 ===")
        if paper:  # 使用之前获取的BERT论文
            print("\n获取引用该论文的文献:")
            citations = await crossref.get_citations(paper.doi)
            for i, citing_paper in enumerate(citations[:3], 1):
                print(f"\n--- 引用论文 {i} ---")
                print(f"标题: {citing_paper.title}")
                print(f"作者: {', '.join(citing_paper.authors)}")
                print(f"发表年份: {citing_paper.year}")

            print("\n获取该论文引用的参考文献:")
            references = await crossref.get_references(paper.doi)
            for i, ref_paper in enumerate(references[:3], 1):
                print(f"\n--- 参考文献 {i} ---")
                print(f"标题: {ref_paper.title}")
                print(f"作者: {', '.join(ref_paper.authors)}")
                print(f"发表年份: {ref_paper.year if ref_paper.year else '未知'}")

        # 示例6：展示venue信息的使用
        print("\n=== 示例6：展示期刊/会议详细信息 ===")
        if papers:
            paper = papers[0]
            print(f"文献类型: {paper.venue_type}")
            print(f"发表venue: {paper.venue_name}")
            if paper.venue_info:
                print("Venue详细信息:")
                for key, value in paper.venue_info.items():
                    if value:
                        print(f"  - {key}: {value}")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())