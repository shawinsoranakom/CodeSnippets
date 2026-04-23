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

                    # 多次降重处理
                    if text_fragments:
                        current_fragments = text_fragments

                        # 进行多轮降重处理
                        for iteration in range(1, self.reduction_times + 1):
                            # 处理当前片段
                            processed_content = yield from self._process_text_fragments(current_fragments, iteration)

                            # 如果这是最后一次迭代，保存结果
                            if iteration == self.reduction_times:
                                final_content = processed_content
                                break

                            # 否则，准备下一轮迭代的片段
                            # 从处理结果中提取处理后的内容
                            next_fragments = []
                            for idx, item in enumerate(self.processed_results):
                                next_fragments.append(TextFragment(
                                    content=item['content'],
                                    fragment_index=idx,
                                    total_fragments=len(self.processed_results)
                                ))

                            current_fragments = next_fragments

                        # 更新UI显示最终结果
                        self.chatbot[-1] = ["处理完成", f"共完成 {self.reduction_times} 轮降重"]
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
            instruction = self.plugin_kwargs.get("advanced_arg", """请对以下学术文本进行彻底改写，以显著降低AI生成特征。具体要求如下：

1. 保持学术写作的严谨性和专业性
2. 维持原文的核心论述和逻辑框架
3. 优化句式结构：
   - 灵活运用主动句与被动句
   - 适当拆分复杂句式，提高可读性
   - 注意句式的多样性，避免重复模式
   - 打破AI常用的句式模板
4. 改善用词：
   - 使用更多学术语境下的同义词替换
   - 避免过于机械和规律性的连接词
   - 适当调整专业术语的表达方式
   - 增加词汇多样性，减少重复用词
5. 增强文本的学术特征：
   - 注重论证的严密性
   - 保持表达的客观性
   - 适度体现作者的学术见解
   - 避免过于完美和均衡的论述结构
6. 确保语言风格的一致性
7. 减少AI生成文本常见的套路和模式""")
            sys_prompt_array = [f"""作为一位专业的学术写作顾问，请按照以下要求改写文本：

1. 严格保持学术写作规范
2. 维持原文的核心论述和逻辑框架
3. 通过优化句式结构和用词降低AI生成特征
4. 确保语言风格的一致性和专业性
5. 保持内容的客观性和准确性
6. 避免AI常见的套路化表达和过于完美的结构"""] * len(sections_to_process)

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