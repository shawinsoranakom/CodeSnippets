def 论文下载(txt: str, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt: 用户输入，可以是DOI、arxiv ID或相关链接，支持多行输入进行批量下载
    """
    from crazy_functions.doc_fns.text_content_loader import TextContentLoader
    from crazy_functions.review_fns.data_sources.arxiv_source import ArxivSource
    from crazy_functions.review_fns.data_sources.scihub_source import SciHub
    # 解析输入
    paper_infos = extract_paper_ids(txt)
    if not paper_infos:
        chatbot.append(["输入解析", "未能识别任何论文ID或DOI，请检查输入格式。支持以下格式：\n- arXiv ID (例如：2103.14030)\n- arXiv链接\n- DOI (例如：10.1234/xxx)\n- DOI链接\n\n多个论文ID请用换行分隔。"])
        yield from update_ui(chatbot=chatbot, history=history)
        return

    # 创建保存目录 - 使用时间戳创建唯一文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_save_dir = get_log_folder(get_user(chatbot), plugin_name='paper_download')
    save_dir = os.path.join(base_save_dir, f"papers_{timestamp}")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = Path(save_dir)

    # 记录下载结果
    success_count = 0
    failed_papers = []
    downloaded_files = []  # 记录成功下载的文件路径

    chatbot.append([f"开始下载", f"支持多行输入下载多篇论文，共检测到 {len(paper_infos)} 篇论文，开始下载..."])
    yield from update_ui(chatbot=chatbot, history=history)

    for id_type, paper_id in paper_infos:
        try:
            if id_type == 'arxiv':
                chatbot.append([f"正在下载", f"从arXiv下载论文 {paper_id}..."])
                yield from update_ui(chatbot=chatbot, history=history)

                # 使用改进的arxiv查询方法
                formatted_id = format_arxiv_id(paper_id)
                paper_result = get_arxiv_paper(formatted_id)

                if not paper_result:
                    failed_papers.append((paper_id, "未找到论文"))
                    continue

                # 下载PDF
                try:
                    filename = f"arxiv_{paper_id.replace('/', '_')}.pdf"
                    pdf_path = str(save_path / filename)
                    paper_result.download_pdf(filename=pdf_path)
                    if os.path.exists(pdf_path):
                        downloaded_files.append(pdf_path)
                except Exception as e:
                    failed_papers.append((paper_id, f"PDF下载失败: {str(e)}"))
                    continue

            else:  # doi
                chatbot.append([f"正在下载", f"从Sci-Hub下载论文 {paper_id}..."])
                yield from update_ui(chatbot=chatbot, history=history)

                sci_hub = SciHub(
                    doi=paper_id,
                    path=save_path
                )
                pdf_path = sci_hub.fetch()
                if pdf_path and os.path.exists(pdf_path):
                    downloaded_files.append(pdf_path)

            # 检查下载结果
            if pdf_path and os.path.exists(pdf_path):
                promote_file_to_downloadzone(pdf_path, chatbot=chatbot)
                success_count += 1
            else:
                failed_papers.append((paper_id, "下载失败"))

        except Exception as e:
            failed_papers.append((paper_id, str(e)))

        yield from update_ui(chatbot=chatbot, history=history)

    # 创建ZIP压缩包
    if downloaded_files:
        try:
            zip_path = create_zip_archive(downloaded_files, Path(base_save_dir))
            promote_file_to_downloadzone(zip_path, chatbot=chatbot)
            chatbot.append([
                f"创建压缩包",
                f"已将所有下载的论文打包为: {os.path.basename(zip_path)}"
            ])
            yield from update_ui(chatbot=chatbot, history=history)
        except Exception as e:
            chatbot.append([
                f"创建压缩包失败",
                f"打包文件时出现错误: {str(e)}"
            ])
            yield from update_ui(chatbot=chatbot, history=history)

    # 生成最终报告
    summary = f"下载完成！成功下载 {success_count} 篇论文。\n"
    if failed_papers:
        summary += "\n以下论文下载失败：\n"
        for paper_id, reason in failed_papers:
            summary += f"- {paper_id}: {reason}\n"

    if downloaded_files:
        summary += f"\n所有论文已存放在文件夹 '{save_dir}' 中，并打包到压缩文件中。您可以在下载区找到单个PDF文件和压缩包。"

    chatbot.append([
        f"下载完成",
        summary
    ])
    yield from update_ui(chatbot=chatbot, history=history)

    # 如果下载成功且用户想要直接阅读内容
    if downloaded_files:
        chatbot.append([
            "提示",
            "正在读取论文内容进行分析，请稍候..."
        ])
        yield from update_ui(chatbot=chatbot, history=history)

        # 使用TextContentLoader加载整个文件夹的PDF文件内容
        loader = TextContentLoader(chatbot, history)

        # 删除提示信息
        chatbot.pop()

        # 加载PDF内容 - 传入文件夹路径而不是单个文件路径
        yield from loader.execute(save_dir)

        # 添加提示信息
        chatbot.append([
            "提示",
            "论文内容已加载完毕，您可以直接向AI提问有关该论文的问题。"
        ])
        yield from update_ui(chatbot=chatbot, history=history)