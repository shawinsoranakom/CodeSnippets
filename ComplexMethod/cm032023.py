def save_results(self, content: str, original_file_path: str) -> List[str]:
        """保存处理结果为多种格式"""
        if not content:
            return []

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        original_filename = os.path.basename(original_file_path)
        filename_without_ext = os.path.splitext(original_filename)[0]
        base_filename = f"{filename_without_ext}_processed_{timestamp}"

        result_files = []

        # 获取用户指定的处理类型
        processing_type = self.plugin_kwargs.get("advanced_arg", "文本处理")

        # 1. 保存为TXT
        try:
            txt_formatter = TxtFormatter()
            txt_content = txt_formatter.create_document(content)
            txt_file = write_history_to_file(
                history=[txt_content],
                file_basename=f"{base_filename}.txt"
            )
            result_files.append(txt_file)
        except Exception as e:
            self.chatbot.append(["警告", f"TXT格式保存失败: {str(e)}"])

        # 2. 保存为Markdown
        try:
            md_formatter = MarkdownFormatter()
            md_content = md_formatter.create_document(content, processing_type)
            md_file = write_history_to_file(
                history=[md_content],
                file_basename=f"{base_filename}.md"
            )
            result_files.append(md_file)
        except Exception as e:
            self.chatbot.append(["警告", f"Markdown格式保存失败: {str(e)}"])

        # 3. 保存为HTML
        try:
            html_formatter = HtmlFormatter(processing_type=processing_type)
            html_content = html_formatter.create_document(content)
            html_file = write_history_to_file(
                history=[html_content],
                file_basename=f"{base_filename}.html"
            )
            result_files.append(html_file)
        except Exception as e:
            self.chatbot.append(["警告", f"HTML格式保存失败: {str(e)}"])

        # 4. 保存为Word
        try:
            word_formatter = WordFormatter()
            doc = word_formatter.create_document(content, processing_type)

            # 获取保存路径
            from toolbox import get_log_folder
            word_path = os.path.join(get_log_folder(), f"{base_filename}.docx")
            doc.save(word_path)

            # 5. 保存为PDF（通过Word转换）
            try:
                from crazy_functions.paper_fns.file2file_doc.word2pdf import WordToPdfConverter
                pdf_path = WordToPdfConverter.convert_to_pdf(word_path)
                result_files.append(pdf_path)
            except Exception as e:
                self.chatbot.append(["警告", f"PDF格式保存失败: {str(e)}"])

        except Exception as e:
            self.chatbot.append(["警告", f"Word格式保存失败: {str(e)}"])

        # 添加到下载区
        for file in result_files:
            promote_file_to_downloadzone(file, chatbot=self.chatbot)

        return result_files