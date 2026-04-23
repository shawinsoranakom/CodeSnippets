def 自定义智能文档处理(txt: str, llm_kwargs: Dict, plugin_kwargs: Dict, chatbot: List,
              history: List, system_prompt: str, user_request: str):
    """主函数 - 文件到文件处理"""
    # 初始化
    processor = DocumentProcessor(llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)
    chatbot.append(["函数插件功能", "文件内容处理：将文档内容按照指定要求处理后输出为多种格式"])
    yield from update_ui(chatbot=chatbot, history=history)

    # 验证输入路径
    if not os.path.exists(txt):
        report_exception(chatbot, history, a=f"解析路径: {txt}", b=f"找不到路径或无权访问: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)
        return

    # 验证路径安全性
    user_name = chatbot.get_user()
    validate_path_safety(txt, user_name)

    # 获取文件列表
    if os.path.isfile(txt):
        # 单个文件处理
        file_paths = [txt]
    else:
        # 目录处理 - 类似批量文件询问插件
        project_folder = txt
        extract_folder = next((d for d in glob.glob(f'{project_folder}/*')
                           if os.path.isdir(d) and d.endswith('.extract')), project_folder)

        # 排除压缩文件
        exclude_patterns = r'/[^/]+\.(zip|rar|7z|tar|gz)$'
        file_paths = [f for f in glob.glob(f'{extract_folder}/**', recursive=True)
                     if os.path.isfile(f) and not re.search(exclude_patterns, f)]

        # 过滤支持的文件格式
        file_paths = [f for f in file_paths if any(f.lower().endswith(ext) for ext in
                    list(processor.paper_extractor.SUPPORTED_EXTENSIONS) + ['.json', '.csv', '.xlsx', '.xls'])]

    if not file_paths:
        report_exception(chatbot, history, a=f"解析路径: {txt}", b="未找到支持的文件类型")
        yield from update_ui(chatbot=chatbot, history=history)
        return

    # 处理文件
    if len(file_paths) > 1:
        chatbot.append(["发现多个文件", f"共找到 {len(file_paths)} 个文件，将处理第一个文件"])
        yield from update_ui(chatbot=chatbot, history=history)

    # 只处理第一个文件
    file_to_process = file_paths[0]
    processed_content = yield from processor.process_file(file_to_process)

    if processed_content:
        # 保存结果
        result_files = processor.save_results(processed_content, file_to_process)

        if result_files:
            chatbot.append(["处理完成", f"已生成 {len(result_files)} 个结果文件"])
        else:
            chatbot.append(["处理完成", "但未能保存任何结果文件"])
    else:
        chatbot.append(["处理失败", "未能生成有效的处理结果"])

    yield from update_ui(chatbot=chatbot, history=history)