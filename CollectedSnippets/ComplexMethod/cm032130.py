async def example_usage():
    """OpenAlexSource使用示例"""
    # 初始化OpenAlexSource
    openalex = OpenAlexSource()

    try:
        print("正在搜索论文...")
        # 搜索与"artificial intelligence"相关的论文，限制返回5篇
        papers = await openalex.search(query="artificial intelligence", limit=5)

        if not papers:
            print("未获取到任何论文信息")
            return

        print(f"找到 {len(papers)} 篇论文")

        # 打印搜索结果
        for i, paper in enumerate(papers, 1):
            print(f"\n--- 论文 {i} ---")
            print(f"标题: {paper.title}")
            print(f"作者: {', '.join(paper.authors) if paper.authors else '未知'}")
            if paper.institutions:
                print(f"机构: {', '.join(paper.institutions)}")
            print(f"发表年份: {paper.year if paper.year else '未知'}")
            print(f"DOI: {paper.doi if paper.doi else '未知'}")
            print(f"URL: {paper.url if paper.url else '未知'}")
            if paper.abstract:
                print(f"摘要: {paper.abstract[:200]}...")
            print(f"引用次数: {paper.citations if paper.citations is not None else '未知'}")
            print(f"发表venue: {paper.venue if paper.venue else '未知'}")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())