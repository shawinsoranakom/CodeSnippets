def execute(self, txt: str) -> Generator:
        """执行文本加载和显示 - 保持原有接口

        Args:
            txt: 目标路径

        Yields:
            Generator: UI更新生成器
        """
        try:
            # 首先显示正在处理的提示信息
            self.chatbot.append(["提示", "正在提取文本内容，请稍作等待..."])
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            user_name = self.chatbot.get_user()
            validate_path_safety(txt, user_name)
            self.start_time = time.time()
            self.processed_size = 0
            self.failed_files.clear()
            successful_files = []
            successful_contents = []

            # 收集文件
            files = self._collect_files(txt)
            if not files:
                # 移除之前的提示信息
                self.chatbot.pop()
                self.chatbot.append(["提示", "未找到任何有效文件"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                return

            # 批量处理文件
            content_blocks = []
            for i in range(0, len(files), self.BATCH_SIZE):
                batch = files[i:i + self.BATCH_SIZE]
                results = self._process_file_batch(batch)

                for file_info, content in results:
                    if content:
                        content_blocks.append(self._format_content_with_fold(file_info, content))
                        successful_files.append(file_info)
                        successful_contents.append(content)

            # 显示文件内容，替换之前的提示信息
            if content_blocks:
                # 移除之前的提示信息
                self.chatbot.pop()
                self.chatbot.append(["文件内容", "\n".join(content_blocks)])
                self.history.extend([
                    self._format_content_for_llm(successful_files, successful_contents),
                    "我已经接收到你上传的文件的内容，请提问"
                ])
                yield from update_ui(chatbot=self.chatbot, history=self.history)

            yield from update_ui(chatbot=self.chatbot, history=self.history)

        except Exception as e:
            # 发生错误时，移除之前的提示信息
            if len(self.chatbot) > 0 and self.chatbot[-1][0] == "提示":
                self.chatbot.pop()
            self.chatbot.append(["错误", f"处理过程中出现错误: {str(e)}"])
            yield from update_ui(chatbot=self.chatbot, history=self.history)

        finally:
            self.executor.shutdown(wait=False)
            self.file_cache.clear()