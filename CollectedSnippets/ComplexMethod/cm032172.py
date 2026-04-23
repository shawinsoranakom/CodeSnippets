def 论文期刊会议推荐(txt: str, llm_kwargs: Dict, plugin_kwargs: Dict, chatbot: List,
                history: List, system_prompt: str, user_request: str):
    """主函数 - 论文期刊会议推荐"""
    # 初始化推荐器
    chatbot.append(["函数插件功能及使用方式", "论文期刊会议推荐：基于论文内容分析，为您推荐合适的学术期刊和会议投稿目标。适用于各个学科专业（自然科学、工程技术、医学、社会科学、人文学科等），根据不同学科的评价标准和发表文化，提供分层次的期刊会议推荐、影响因子分析、发表难度评估、投稿策略建议等。<br><br>📋 使用方式：<br>1、直接上传PDF文件<br>2、输入DOI号或arXiv ID<br>3、点击插件开始分析"])
    yield from update_ui(chatbot=chatbot, history=history)

    paper_file = None

    # 检查输入是否为论文ID（arxiv或DOI）
    paper_info = extract_paper_id(txt)

    if paper_info:
        # 如果是论文ID，下载论文
        chatbot.append(["检测到论文ID", f"检测到{'arXiv' if paper_info[0] == 'arxiv' else 'DOI'} ID: {paper_info[1]}，准备下载论文..."])
        yield from update_ui(chatbot=chatbot, history=history)

        # 下载论文
        paper_file = download_paper_by_id(paper_info, chatbot, history)

        if not paper_file:
            report_exception(chatbot, history, a=f"下载论文失败", b=f"无法下载{'arXiv' if paper_info[0] == 'arxiv' else 'DOI'}论文: {paper_info[1]}")
            yield from update_ui(chatbot=chatbot, history=history)
            return
    else:
        # 检查输入路径
        if not os.path.exists(txt):
            report_exception(chatbot, history, a=f"解析论文: {txt}", b=f"找不到文件或无权访问: {txt}")
            yield from update_ui(chatbot=chatbot, history=history)
            return

        # 验证路径安全性
        user_name = chatbot.get_user()
        validate_path_safety(txt, user_name)

        # 查找论文文件
        paper_file = _find_paper_file(txt)

        if not paper_file:
            report_exception(chatbot, history, a=f"解析论文", b=f"在路径 {txt} 中未找到支持的论文文件")
            yield from update_ui(chatbot=chatbot, history=history)
            return

    yield from update_ui(chatbot=chatbot, history=history)

    # 确保paper_file是字符串
    if paper_file is not None and not isinstance(paper_file, str):
        # 尝试转换为字符串
        try:
            paper_file = str(paper_file)
        except:
            report_exception(chatbot, history, a=f"类型错误", b=f"论文路径不是有效的字符串: {type(paper_file)}")
            yield from update_ui(chatbot=chatbot, history=history)
            return

    # 开始推荐
    chatbot.append(["开始分析", f"正在分析论文并生成期刊会议推荐: {os.path.basename(paper_file)}"])
    yield from update_ui(chatbot=chatbot, history=history)

    recommender = JournalConferenceRecommender(llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)
    yield from recommender.recommend_venues(paper_file)