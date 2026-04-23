def _process_structured_paper(self, file_path: str) -> Generator:
        """处理结构化论文文件"""
        # 1. 提取论文结构
        self.chatbot[-1] = ["正在分析论文结构", f"文件路径: {file_path}"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        try:
            paper = self.paper_extractor.extract_paper_structure(file_path)

            if not paper or not paper.sections:
                self.chatbot.append(["无法提取论文结构", "将使用全文内容进行处理"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)

                # 使用全文内容进行段落切分
                if paper and paper.full_text:
                    # 使用增强的分割函数进行更细致的分割
                    fragments = self._breakdown_section_content(paper.full_text)

                    # 创建文本片段对象
                    text_fragments = []
                    for i, frag in enumerate(fragments):
                        if frag.strip():
                            text_fragments.append(TextFragment(
                                content=frag,
                                fragment_index=i,
                                total_fragments=len(fragments)
                            ))

                    # 批量处理片段
                    if text_fragments:
                        self.chatbot[-1] = ["开始处理文本", f"共 {len(text_fragments)} 个片段"]
                        yield from update_ui(chatbot=self.chatbot, history=self.history)

                        # 一次性准备所有输入
                        inputs_array, inputs_show_user_array, history_array = self._create_batch_inputs(text_fragments)

                        # 使用系统提示
                        instruction = self.plugin_kwargs.get("advanced_arg", "请润色以下学术文本，提高其语言表达的准确性、专业性和流畅度，保持学术风格，确保逻辑连贯，但不改变原文的科学内容和核心观点")
                        sys_prompt_array = [f"你是一个专业的学术文献编辑助手。请按照用户的要求：'{instruction}'处理文本。保持学术风格，增强表达的准确性和专业性。"] * len(text_fragments)

                        # 调用LLM一次性处理所有片段
                        response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
                            inputs_array=inputs_array,
                            inputs_show_user_array=inputs_show_user_array,
                            llm_kwargs=self.llm_kwargs,
                            chatbot=self.chatbot,
                            history_array=history_array,
                            sys_prompt_array=sys_prompt_array,
                        )

                        # 处理响应
                        for j, frag in enumerate(text_fragments):
                            try:
                                llm_response = response_collection[j * 2 + 1]
                                processed_text = self._extract_decision(llm_response)

                                if processed_text and processed_text.strip():
                                    self.processed_results.append({
                                        'index': frag.fragment_index,
                                        'content': processed_text
                                    })
                                else:
                                    self.failed_fragments.append(frag)
                                    self.processed_results.append({
                                        'index': frag.fragment_index,
                                        'content': frag.content
                                    })
                            except Exception as e:
                                self.failed_fragments.append(frag)
                                self.processed_results.append({
                                    'index': frag.fragment_index,
                                    'content': frag.content
                                })

                        # 按原始顺序合并结果
                        self.processed_results.sort(key=lambda x: x['index'])
                        final_content = "\n".join([item['content'] for item in self.processed_results])

                        # 更新UI
                        success_count = len(text_fragments) - len(self.failed_fragments)
                        self.chatbot[-1] = ["处理完成", f"成功处理 {success_count}/{len(text_fragments)} 个片段"]
                        yield from update_ui(chatbot=self.chatbot, history=self.history)

                        return final_content
                    else:
                        self.chatbot.append(["处理失败", "未能提取到有效的文本内容"])
                        yield from update_ui(chatbot=self.chatbot, history=self.history)
                        return None
                else:
                    self.chatbot.append(["处理失败", "未能提取到论文内容"])
                    yield from update_ui(chatbot=self.chatbot, history=self.history)
                    return None

            # 2. 准备处理章节内容（不处理标题）
            self.chatbot[-1] = ["已提取论文结构", f"共 {len(paper.sections)} 个主要章节"]
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            # 3. 收集所有需要处理的章节内容并分割为合适大小
            sections_to_process = []
            section_map = {}  # 用于映射处理前后的内容

            def collect_section_contents(sections, parent_path=""):
                """递归收集章节内容，跳过参考文献部分"""
                for i, section in enumerate(sections):
                    current_path = f"{parent_path}/{i}" if parent_path else f"{i}"

                    # 检查是否为参考文献部分，如果是则跳过
                    if section.section_type == 'references' or section.title.lower() in ['references', '参考文献', 'bibliography', '文献']:
                        continue  # 跳过参考文献部分

                    # 只处理内容非空的章节
                    if section.content and section.content.strip():
                        # 使用增强的分割函数进行更细致的分割
                        fragments = self._breakdown_section_content(section.content)

                        for fragment_idx, fragment_content in enumerate(fragments):
                            if fragment_content.strip():
                                fragment_index = len(sections_to_process)
                                sections_to_process.append(TextFragment(
                                    content=fragment_content,
                                    fragment_index=fragment_index,
                                    total_fragments=0  # 临时值，稍后更新
                                ))

                                # 保存映射关系，用于稍后更新章节内容
                                # 为每个片段存储原始章节和片段索引信息
                                section_map[fragment_index] = (current_path, section, fragment_idx, len(fragments))

                    # 递归处理子章节
                    if section.subsections:
                        collect_section_contents(section.subsections, current_path)

            # 收集所有章节内容
            collect_section_contents(paper.sections)

            # 更新总片段数
            total_fragments = len(sections_to_process)
            for frag in sections_to_process:
                frag.total_fragments = total_fragments

            # 4. 如果没有内容需要处理，直接返回
            if not sections_to_process:
                self.chatbot.append(["处理完成", "未找到需要处理的内容"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                return None

            # 5. 批量处理章节内容
            self.chatbot[-1] = ["开始处理论文内容", f"共 {len(sections_to_process)} 个内容片段"]
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            # 一次性准备所有输入
            inputs_array, inputs_show_user_array, history_array = self._create_batch_inputs(sections_to_process)

            # 使用系统提示
            instruction = self.plugin_kwargs.get("advanced_arg", "请润色以下学术文本，提高其语言表达的准确性、专业性和流畅度，保持学术风格，确保逻辑连贯，但不改变原文的科学内容和核心观点")
            sys_prompt_array = [f"你是一个专业的学术文献编辑助手。请按照用户的要求：'{instruction}'处理文本。保持学术风格，增强表达的准确性和专业性。"] * len(sections_to_process)

            # 调用LLM一次性处理所有片段
            response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
                inputs_array=inputs_array,
                inputs_show_user_array=inputs_show_user_array,
                llm_kwargs=self.llm_kwargs,
                chatbot=self.chatbot,
                history_array=history_array,
                sys_prompt_array=sys_prompt_array,
            )

            # 处理响应，重组章节内容
            section_contents = {}  # 用于重组各章节的处理后内容

            for j, frag in enumerate(sections_to_process):
                try:
                    llm_response = response_collection[j * 2 + 1]
                    processed_text = self._extract_decision(llm_response)

                    if processed_text and processed_text.strip():
                        # 保存处理结果
                        self.processed_results.append({
                            'index': frag.fragment_index,
                            'content': processed_text
                        })

                        # 存储处理后的文本片段，用于后续重组
                        fragment_index = frag.fragment_index
                        if fragment_index in section_map:
                            path, section, fragment_idx, total_fragments = section_map[fragment_index]

                            # 初始化此章节的内容容器（如果尚未创建）
                            if path not in section_contents:
                                section_contents[path] = [""] * total_fragments

                            # 将处理后的片段放入正确位置
                            section_contents[path][fragment_idx] = processed_text
                    else:
                        self.failed_fragments.append(frag)
                except Exception as e:
                    self.failed_fragments.append(frag)

            # 重组每个章节的内容
            for path, fragments in section_contents.items():
                section = None
                for idx in section_map:
                    if section_map[idx][0] == path:
                        section = section_map[idx][1]
                        break

                if section:
                    # 合并该章节的所有处理后片段
                    section.content = "\n".join(fragments)

            # 6. 更新UI
            success_count = total_fragments - len(self.failed_fragments)
            self.chatbot[-1] = ["处理完成", f"成功处理 {success_count}/{total_fragments} 个内容片段"]
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            # 收集参考文献部分（不进行处理）
            references_sections = []
            def collect_references(sections, parent_path=""):
                """递归收集参考文献部分"""
                for i, section in enumerate(sections):
                    current_path = f"{parent_path}/{i}" if parent_path else f"{i}"

                    # 检查是否为参考文献部分
                    if section.section_type == 'references' or section.title.lower() in ['references', '参考文献', 'bibliography', '文献']:
                        references_sections.append((current_path, section))

                    # 递归检查子章节
                    if section.subsections:
                        collect_references(section.subsections, current_path)

            # 收集参考文献
            collect_references(paper.sections)

            # 7. 将处理后的结构化论文转换为Markdown
            markdown_content = self.paper_extractor.generate_markdown(paper)

            # 8. 返回处理后的内容
            self.chatbot[-1] = ["处理完成", f"成功处理 {success_count}/{total_fragments} 个内容片段，参考文献部分未处理"]
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            return markdown_content

        except Exception as e:
            self.chatbot.append(["结构化处理失败", f"错误: {str(e)}，将尝试作为普通文件处理"])
            yield from update_ui(chatbot=self.chatbot, history=self.history)
            return (yield from self._process_regular_file(file_path))