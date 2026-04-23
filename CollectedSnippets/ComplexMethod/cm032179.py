def GitHub项目智能检索(txt: str, llm_kwargs: Dict, plugin_kwargs: Dict, chatbot: List,
           history: List, system_prompt: str, user_request: str):
    """GitHub项目智能检索主函数"""

    # 初始化GitHub API调用源
    github_source = GitHubSource(api_key=plugin_kwargs.get("github_api_key"))

    # 初始化处理器
    handlers = {
        "repo": RepositoryHandler(github_source, llm_kwargs),
        "code": CodeSearchHandler(github_source, llm_kwargs),
        "user": UserSearchHandler(github_source, llm_kwargs),
        "topic": TopicHandler(github_source, llm_kwargs),
    }

    # 分析查询意图
    chatbot.append(["分析查询意图", "正在分析您的查询需求..."])
    yield from update_ui(chatbot=chatbot, history=history)

    query_analyzer = QueryAnalyzer()
    search_criteria = yield from query_analyzer.analyze_query(
        txt, chatbot, llm_kwargs
    )

    # 根据查询类型选择处理器
    handler = handlers.get(search_criteria.query_type)
    if not handler:
        handler = handlers["repo"]  # 默认使用仓库处理器

    # 处理查询
    chatbot.append(["开始搜索", f"使用{handler.__class__.__name__}处理您的请求，正在搜索GitHub..."])
    yield from update_ui(chatbot=chatbot, history=history)

    final_prompt = asyncio.run(handler.handle(
        criteria=search_criteria,
        chatbot=chatbot,
        history=history,
        system_prompt=system_prompt,
        llm_kwargs=llm_kwargs,
        plugin_kwargs=plugin_kwargs
    ))

    if final_prompt:
        # 检查是否是道歉提示
        if "很抱歉，我们未能找到" in final_prompt:
            chatbot.append([txt, final_prompt])
            yield from update_ui(chatbot=chatbot, history=history)
            return

        # 在 final_prompt 末尾添加用户原始查询要求
        final_prompt += f"""

原始用户查询: "{txt}"

重要提示:
- 你的回答必须直接满足用户的原始查询要求
- 在遵循之前指南的同时，优先回答用户明确提出的问题
- 确保回答格式和内容与用户期望一致
- 对于GitHub仓库需要提供链接地址, 回复中请采用以下格式的HTML链接:
  * 对于GitHub仓库: <a href='Github_URL' target='_blank'>仓库名</a>
- 不要生成参考列表，引用信息将另行处理
"""

        # 使用最终的prompt生成回答
        response = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=final_prompt,
            inputs_show_user=txt,
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history=[],
            sys_prompt=f"你是一个熟悉GitHub生态系统的专业助手，能帮助用户找到合适的项目、代码和开发者。除非用户指定，否则请使用中文回复。"
        )

        # 1. 获取项目列表
        repos_list = handler.ranked_repos  # 直接使用原始仓库数据

        # 在新的对话中添加格式化的仓库参考列表
        if repos_list:
            references = ""
            for idx, repo in enumerate(repos_list, 1):
                # 构建仓库引用
                stars_str = f"⭐ {repo.get('stargazers_count', 'N/A')}" if repo.get('stargazers_count') else ""
                forks_str = f"🍴 {repo.get('forks_count', 'N/A')}" if repo.get('forks_count') else ""
                stats = f"{stars_str} {forks_str}".strip()
                stats = f" ({stats})" if stats else ""

                language = f" [{repo.get('language', '')}]" if repo.get('language') else ""

                reference = f"[{idx}] **{repo.get('name', '')}**{language}{stats}  \n"
                reference += f"👤 {repo.get('owner', {}).get('login', 'N/A') if repo.get('owner') is not None else 'N/A'} | "
                reference += f"📅 {repo.get('updated_at', 'N/A')[:10]} | "
                reference += f"<a href='{repo.get('html_url', '')}' target='_blank'>GitHub</a>  \n"

                if repo.get('description'):
                    reference += f"{repo.get('description')}  \n"
                reference += "  \n"

                references += reference

            # 添加新的对话显示参考仓库
            chatbot.append(["推荐项目如下：", references])
            yield from update_ui(chatbot=chatbot, history=history)

        # 2. 保存结果到文件
        # 创建保存目录
        save_dir = get_log_folder(get_user(chatbot), plugin_name='github_search')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 生成文件名
        def get_safe_filename(txt, max_length=10):
            # 获取文本前max_length个字符作为文件名
            filename = txt[:max_length].strip()
            # 移除不安全的文件名字符
            filename = re.sub(r'[\\/:*?"<>|]', '', filename)
            # 如果文件名为空，使用时间戳
            if not filename:
                filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            return filename

        base_filename = get_safe_filename(txt)

        # 准备保存的内容 - 优化文档结构
        md_content = f"# GitHub搜索结果: {txt}\n\n"
        md_content += f"搜索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 添加模型回复
        md_content += "## 搜索分析与总结\n\n"
        md_content += response + "\n\n"

        # 添加所有搜索到的仓库详细信息
        md_content += "## 推荐项目详情\n\n"

        if not repos_list:
            md_content += "未找到匹配的项目\n\n"
        else:
            md_content += f"共找到 {len(repos_list)} 个相关项目\n\n"

            # 添加项目简表
            md_content += "### 项目一览表\n\n"
            md_content += "| 序号 | 项目名称 | 作者 | 语言 | 星标数 | 更新时间 |\n"
            md_content += "| ---- | -------- | ---- | ---- | ------ | -------- |\n"

            for idx, repo in enumerate(repos_list, 1):
                md_content += f"| {idx} | [{repo.get('name', '')}]({repo.get('html_url', '')}) | {repo.get('owner', {}).get('login', 'N/A') if repo.get('owner') is not None else 'N/A'} | {repo.get('language', 'N/A')} | {repo.get('stargazers_count', 'N/A')} | {repo.get('updated_at', 'N/A')[:10]} |\n"

            md_content += "\n"

            # 添加详细项目信息
            md_content += "### 项目详细信息\n\n"
            for idx, repo in enumerate(repos_list, 1):
                md_content += f"#### {idx}. {repo.get('name', '')}\n\n"
                md_content += f"- **仓库**: [{repo.get('full_name', '')}]({repo.get('html_url', '')})\n"
                md_content += f"- **作者**: [{repo.get('owner', {}).get('login', '') if repo.get('owner') is not None else 'N/A'}]({repo.get('owner', {}).get('html_url', '') if repo.get('owner') is not None else '#'})\n"
                md_content += f"- **描述**: {repo.get('description', 'N/A')}\n"
                md_content += f"- **语言**: {repo.get('language', 'N/A')}\n"
                md_content += f"- **星标**: {repo.get('stargazers_count', 'N/A')}\n"
                md_content += f"- **Fork数**: {repo.get('forks_count', 'N/A')}\n"
                md_content += f"- **最近更新**: {repo.get('updated_at', 'N/A')[:10]}\n"
                md_content += f"- **创建时间**: {repo.get('created_at', 'N/A')[:10]}\n"
                md_content += f"- **开源许可**: {repo.get('license', {}).get('name', 'N/A') if repo.get('license') is not None else 'N/A'}\n"
                if repo.get('topics'):
                    md_content += f"- **主题标签**: {', '.join(repo.get('topics', []))}\n"
                if repo.get('homepage'):
                    md_content += f"- **项目主页**: [{repo.get('homepage')}]({repo.get('homepage')})\n"
                md_content += "\n"

        # 添加查询信息和元数据
        md_content += "## 查询元数据\n\n"
        md_content += f"- **原始查询**: {txt}\n"
        md_content += f"- **查询类型**: {search_criteria.query_type}\n"
        md_content += f"- **关键词**: {', '.join(search_criteria.keywords) if hasattr(search_criteria, 'keywords') and search_criteria.keywords else 'N/A'}\n"
        md_content += f"- **搜索日期**: {datetime.now().strftime('%Y-%m-%d')}\n\n"

        # 保存为多种格式
        saved_files = []
        failed_files = []

        # 1. 保存为TXT
        try:
            txt_formatter = TxtFormatter()
            txt_content = txt_formatter.create_document(md_content)
            txt_file = os.path.join(save_dir, f"github_results_{base_filename}.txt")
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            promote_file_to_downloadzone(txt_file, chatbot=chatbot)
            saved_files.append("TXT")
        except Exception as e:
            failed_files.append(f"TXT (错误: {str(e)})")

        # 2. 保存为Markdown
        try:
            md_formatter = MarkdownFormatter()
            formatted_md_content = md_formatter.create_document(md_content, "GitHub项目搜索")
            md_file = os.path.join(save_dir, f"github_results_{base_filename}.md")
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(formatted_md_content)
            promote_file_to_downloadzone(md_file, chatbot=chatbot)
            saved_files.append("Markdown")
        except Exception as e:
            failed_files.append(f"Markdown (错误: {str(e)})")

        # 3. 保存为HTML
        try:
            html_formatter = HtmlFormatter(processing_type="GitHub项目搜索")
            html_content = html_formatter.create_document(md_content)
            html_file = os.path.join(save_dir, f"github_results_{base_filename}.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            promote_file_to_downloadzone(html_file, chatbot=chatbot)
            saved_files.append("HTML")
        except Exception as e:
            failed_files.append(f"HTML (错误: {str(e)})")

        # 4. 保存为Word
        word_file = None
        try:
            word_formatter = WordFormatter()
            doc = word_formatter.create_document(md_content, "GitHub项目搜索")
            word_file = os.path.join(save_dir, f"github_results_{base_filename}.docx")
            doc.save(word_file)
            promote_file_to_downloadzone(word_file, chatbot=chatbot)
            saved_files.append("Word")
        except Exception as e:
            failed_files.append(f"Word (错误: {str(e)})")
            word_file = None

        # 5. 保存为PDF (仅当Word保存成功时)
        if word_file and os.path.exists(word_file):
            try:
                pdf_file = WordToPdfConverter.convert_to_pdf(word_file)
                promote_file_to_downloadzone(pdf_file, chatbot=chatbot)
                saved_files.append("PDF")
            except Exception as e:
                failed_files.append(f"PDF (错误: {str(e)})")

        # 报告保存结果
        if saved_files:
            success_message = f"成功保存以下格式: {', '.join(saved_files)}"
            if failed_files:
                failure_message = f"以下格式保存失败: {', '.join(failed_files)}"
                chatbot.append(["部分格式保存成功", f"{success_message}。{failure_message}"])
            else:
                chatbot.append(["所有格式保存成功", success_message])
        else:
            chatbot.append(["保存失败", f"所有格式均保存失败: {', '.join(failed_files)}"])
    else:
        report_exception(chatbot, history, a=f"处理失败", b=f"请尝试其他查询")
        yield from update_ui(chatbot=chatbot, history=history)