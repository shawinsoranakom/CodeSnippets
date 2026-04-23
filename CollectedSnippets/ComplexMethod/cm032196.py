async def example_usage():
    """演示WikipediaAPI的使用方法"""
    # 创建默认中文维基百科API客户端
    wiki_zh = WikipediaAPI(language="zh")

    try:
        # 示例1: 基本搜索
        print("\n=== 示例1: 搜索维基百科 ===")
        results = await wiki_zh.search("人工智能", limit=3)

        for i, result in enumerate(results, 1):
            print(f"\n--- 结果 {i} ---")
            print(f"标题: {result.get('title')}")
            snippet = result.get('snippet', '')
            # 清理HTML标签
            snippet = re.sub(r'<.*?>', '', snippet)
            print(f"摘要: {snippet}")
            print(f"字数: {result.get('wordcount')}")
            print(f"大小: {result.get('size')} 字节")

        # 示例2: 获取页面摘要
        print("\n=== 示例2: 获取页面摘要 ===")
        summary = await wiki_zh.get_summary("深度学习", sentences=2)
        print(f"深度学习摘要: {summary}")

        # 示例3: 获取页面内容
        print("\n=== 示例3: 获取页面内容 ===")
        content = await wiki_zh.get_page_content("机器学习")
        if content and "text" in content:
            text = content["text"].get("*", "")
            # 移除HTML标签以便控制台显示
            clean_text = re.sub(r'<.*?>', '', text)
            print(f"机器学习页面内容片段: {clean_text[:200]}...")

            # 显示页面包含的分类数量
            categories = content.get("categories", [])
            print(f"分类数量: {len(categories)}")

            # 显示页面包含的链接数量
            links = content.get("links", [])
            print(f"链接数量: {len(links)}")

        # 示例4: 获取特定章节内容
        print("\n=== 示例4: 获取特定章节内容 ===")
        # 获取引言部分(通常是0号章节)
        intro_content = await wiki_zh.get_page_content("人工智能", section=0)
        if intro_content and "text" in intro_content:
            intro_text = intro_content["text"].get("*", "")
            clean_intro = re.sub(r'<.*?>', '', intro_text)
            print(f"人工智能引言内容片段: {clean_intro[:200]}...")

        # 示例5: 获取随机文章
        print("\n=== 示例5: 获取随机文章 ===")
        random_articles = await wiki_zh.get_random_articles(count=2)
        print("随机文章:")
        for i, article in enumerate(random_articles, 1):
            print(f"{i}. {article.get('title')}")

            # 显示随机文章的简短摘要
            article_summary = await wiki_zh.get_summary(article.get('title'), sentences=1)
            print(f"   摘要: {article_summary[:100]}...")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())