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

        # 4. 多轮降重处理
        if not text_fragments:
            self.chatbot.append(["处理失败", "未能提取到有效的文本内容"])
            yield from update_ui(chatbot=self.chatbot, history=self.history)
            return None

        # 批处理大小
        batch_size = 8  # 每批处理的片段数

        # 第一次迭代
        current_batches = []
        for i in range(0, len(text_fragments), batch_size):
            current_batches.append(text_fragments[i:i + batch_size])

        all_processed_fragments = []

        # 进行多轮降重处理
        for iteration in range(1, self.reduction_times + 1):
            self.chatbot[-1] = ["开始处理文本", f"第 {iteration}/{self.reduction_times} 次降重"]
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            next_batches = []
            all_processed_fragments = []

            # 分批处理当前迭代的片段
            for batch in current_batches:
                # 处理当前批次
                _ = yield from self._process_text_fragments(batch, iteration)

                # 收集处理结果
                processed_batch = []
                for item in self.processed_results:
                    processed_batch.append(TextFragment(
                        content=item['content'],
                        fragment_index=len(all_processed_fragments) + len(processed_batch),
                        total_fragments=0  # 临时值，稍后更新
                    ))

                all_processed_fragments.extend(processed_batch)

                # 如果不是最后一轮迭代，准备下一批次
                if iteration < self.reduction_times:
                    for i in range(0, len(processed_batch), batch_size):
                        next_batches.append(processed_batch[i:i + batch_size])

            # 更新总片段数
            for frag in all_processed_fragments:
                frag.total_fragments = len(all_processed_fragments)

            # 为下一轮迭代准备批次
            current_batches = next_batches

        # 合并最终结果
        final_content = "\n\n".join([frag.content for frag in all_processed_fragments])

        # 5. 更新UI显示最终结果
        self.chatbot[-1] = ["处理完成", f"共完成 {self.reduction_times} 轮降重"]
        yield from update_ui(chatbot=self.chatbot, history=self.history)

        return final_content