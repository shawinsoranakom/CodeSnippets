def _process_regular_file(self, file_path: str) -> Generator:
        """使用原有方式处理普通文件"""
        # 原有的文件处理逻辑
        self.chatbot[-1] = ["正在读取文件", f"文件路径: {file_path}"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        content = extract_text(file_path)
        if not content or not content.strip():
            self.chatbot.append(["处理失败", "文件内容为空或无法提取内容"])
            yield from update_ui(chatbot=self.chatbot, history=self.history)
            return None

        # 2. 分割文本
        self.chatbot[-1] = ["正在分析文件", "将文件内容分割为适当大小的片段"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        # 使用增强的分割函数
        fragments = self._breakdown_section_content(content)

        # 3. 创建文本片段对象
        text_fragments = []
        for i, frag in enumerate(fragments):
            if frag.strip():
                text_fragments.append(TextFragment(
                    content=frag,
                    fragment_index=i,
                    total_fragments=len(fragments)
                ))

        # 4. 处理所有片段
        self.chatbot[-1] = ["开始处理文本", f"共 {len(text_fragments)} 个片段"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        # 批量处理片段
        batch_size = 8  # 每批处理的片段数
        for i in range(0, len(text_fragments), batch_size):
            batch = text_fragments[i:i + batch_size]

            inputs_array, inputs_show_user_array, history_array = self._create_batch_inputs(batch)

            # 使用系统提示
            instruction = self.plugin_kwargs.get("advanced_arg", "请润色以下文本")
            sys_prompt_array = [f"你是一个专业的文本处理助手。请按照用户的要求：'{instruction}'处理文本。"] * len(batch)

            # 调用LLM处理
            response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
                inputs_array=inputs_array,
                inputs_show_user_array=inputs_show_user_array,
                llm_kwargs=self.llm_kwargs,
                chatbot=self.chatbot,
                history_array=history_array,
                sys_prompt_array=sys_prompt_array,
            )

            # 处理响应
            for j, frag in enumerate(batch):
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
                            'content': frag.content  # 如果处理失败，使用原始内容
                        })
                except Exception as e:
                    self.failed_fragments.append(frag)
                    self.processed_results.append({
                        'index': frag.fragment_index,
                        'content': frag.content  # 如果处理失败，使用原始内容
                    })

        # 5. 按原始顺序合并结果
        self.processed_results.sort(key=lambda x: x['index'])
        final_content = "\n".join([item['content'] for item in self.processed_results])

        # 6. 更新UI
        success_count = len(text_fragments) - len(self.failed_fragments)
        self.chatbot[-1] = ["处理完成", f"成功处理 {success_count}/{len(text_fragments)} 个片段"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        return final_content