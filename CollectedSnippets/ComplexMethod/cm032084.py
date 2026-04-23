def execute_single_file(self, file_path: str) -> Generator:
        """执行单个文件的加载和显示

        Args:
            file_path: 文件路径

        Yields:
            Generator: UI更新生成器
        """
        try:
            # 首先显示正在处理的提示信息
            self.chatbot.append(["提示", "正在提取文本内容，请稍作等待..."])
            yield from update_ui(chatbot=self.chatbot, history=self.history)

            user_name = self.chatbot.get_user()
            validate_path_safety(file_path, user_name)
            self.start_time = time.time()
            self.processed_size = 0
            self.failed_files.clear()

            # 验证文件是否存在且可读
            if not os.path.isfile(file_path):
                self.chatbot.pop()
                self.chatbot.append(["错误", f"指定路径不是文件: {file_path}"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                return

            if not self._is_valid_file(file_path):
                self.chatbot.pop()
                self.chatbot.append(["错误", f"无效的文件类型或无法读取: {file_path}"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                return

            # 创建文件信息
            try:
                stats = os.stat(file_path)
                file_size = stats.st_size / (1024 * 1024)  # 转换为MB

                if file_size * 1024 * 1024 > self.MAX_FILE_SIZE:
                    self.chatbot.pop()
                    self.chatbot.append(["错误", f"文件过大（{file_size:.2f}MB > {self.MAX_FILE_SIZE / (1024 * 1024)}MB）"])
                    yield from update_ui(chatbot=self.chatbot, history=self.history)
                    return

                file_info = FileInfo(
                    path=file_path,
                    rel_path=os.path.basename(file_path),
                    size=file_size,
                    extension=os.path.splitext(file_path)[1].lower(),
                    last_modified=time.strftime('%Y-%m-%d %H:%M:%S',
                                              time.localtime(stats.st_mtime))
                )
            except Exception as e:
                self.chatbot.pop()
                self.chatbot.append(["错误", f"处理文件失败: {str(e)}"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                return

            # 读取文件内容
            try:
                content = self._read_file_content(file_info)
                if not content:
                    self.chatbot.pop()
                    self.chatbot.append(["提示", f"文件内容为空或无法提取: {file_path}"])
                    yield from update_ui(chatbot=self.chatbot, history=self.history)
                    return
            except Exception as e:
                self.chatbot.pop()
                self.chatbot.append(["错误", f"读取文件失败: {str(e)}"])
                yield from update_ui(chatbot=self.chatbot, history=self.history)
                return

            # 格式化内容并更新UI
            formatted_content = self._format_content_with_fold(file_info, content)

            # 移除之前的提示信息
            self.chatbot.pop()
            self.chatbot.append(["文件内容", formatted_content])

            # 更新历史记录，便于LLM处理
            llm_content = self._format_content_for_llm([file_info], [content])
            self.history.extend([llm_content, "我已经接收到你上传的文件的内容，请提问"])

            yield from update_ui(chatbot=self.chatbot, history=self.history)

        except Exception as e:
            # 发生错误时，移除之前的提示信息
            if len(self.chatbot) > 0 and self.chatbot[-1][0] == "提示":
                self.chatbot.pop()
            self.chatbot.append(["错误", f"处理过程中出现错误: {str(e)}"])
            yield from update_ui(chatbot=self.chatbot, history=self.history)