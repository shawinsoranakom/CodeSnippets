def download_paper_by_id(paper_info, chatbot, history) -> str:
    """下载论文并返回保存路径

    Args:
        paper_info: 元组，包含论文ID类型（arxiv或doi）和ID值
        chatbot: 聊天机器人对象
        history: 历史记录

    Returns:
        str: 下载的论文路径或None
    """
    from crazy_functions.review_fns.data_sources.scihub_source import SciHub
    id_type, paper_id = paper_info

    # 创建保存目录 - 使用时间戳创建唯一文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    user_name = chatbot.get_user() if hasattr(chatbot, 'get_user') else "default"
    from toolbox import get_log_folder, get_user
    base_save_dir = get_log_folder(get_user(chatbot), plugin_name='paper_download')
    save_dir = os.path.join(base_save_dir, f"papers_{timestamp}")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = Path(save_dir)

    chatbot.append([f"下载论文", f"正在下载{'arXiv' if id_type == 'arxiv' else 'DOI'} {paper_id} 的论文..."])
    update_ui(chatbot=chatbot, history=history)

    pdf_path = None

    try:
        if id_type == 'arxiv':
            # 使用改进的arxiv查询方法
            formatted_id = format_arxiv_id(paper_id)
            paper_result = get_arxiv_paper(formatted_id)

            if not paper_result:
                chatbot.append([f"下载失败", f"未找到arXiv论文: {paper_id}"])
                update_ui(chatbot=chatbot, history=history)
                return None

            # 下载PDF
            filename = f"arxiv_{paper_id.replace('/', '_')}.pdf"
            pdf_path = str(save_path / filename)
            paper_result.download_pdf(filename=pdf_path)

        else:  # doi
            # 下载DOI
            sci_hub = SciHub(
                doi=paper_id,
                path=save_path
            )
            pdf_path = sci_hub.fetch()

        # 检查下载结果
        if pdf_path and os.path.exists(pdf_path):
            promote_file_to_downloadzone(pdf_path, chatbot=chatbot)
            chatbot.append([f"下载成功", f"已成功下载论文: {os.path.basename(pdf_path)}"])
            update_ui(chatbot=chatbot, history=history)
            return pdf_path
        else:
            chatbot.append([f"下载失败", f"论文下载失败: {paper_id}"])
            update_ui(chatbot=chatbot, history=history)
            return None

    except Exception as e:
        chatbot.append([f"下载错误", f"下载论文时出错: {str(e)}"])
        update_ui(chatbot=chatbot, history=history)
        return None