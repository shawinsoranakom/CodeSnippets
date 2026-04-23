def convert_to_markdown(
            self,
            file_path: Union[str, Path],
            output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """将 PDF 转换为 Markdown

        Args:
            file_path: PDF 文件路径
            output_path: 输出 Markdown 文件路径，如果为 None 则返回内容而不保存

        Returns:
            str: 转换后的 Markdown 内容

        Raises:
            Exception: 转换过程中的错误
        """
        try:
            path = self._validate_file(file_path)
            self.logger.info(f"处理: {path}")

            if not self.markitdown_available:
                raise ImportError("markitdown 库未安装，无法进行转换")

            # 导入 markitdown 库
            from markitdown import MarkItDown

            # 准备输出目录
            if output_path:
                output_path = Path(output_path)
                output_dir = output_path.parent
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                # 创建临时目录作为输出目录
                temp_dir = tempfile.mkdtemp()
                output_dir = Path(temp_dir)
                output_path = output_dir / f"{path.stem}.md"

            # 图片目录
            image_dir = output_dir / self.config.image_dir
            image_dir.mkdir(parents=True, exist_ok=True)

            # 创建 MarkItDown 实例并进行转换
            if self.config.docintel_endpoint:
                md = MarkItDown(docintel_endpoint=self.config.docintel_endpoint)
            elif self.config.llm_client and self.config.llm_model:
                md = MarkItDown(
                    enable_plugins=self.config.enable_plugins,
                    llm_client=self.config.llm_client,
                    llm_model=self.config.llm_model
                )
            else:
                md = MarkItDown(enable_plugins=self.config.enable_plugins)

            # 执行转换
            result = md.convert(str(path))
            markdown_content = result.text_content

            # 清理文本
            markdown_content = self._cleanup_text(markdown_content)

            # 如果需要保存到文件
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                self.logger.info(f"转换成功，输出到: {output_path}")

            return markdown_content

        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            raise
        finally:
            # 如果使用了临时目录且没有指定输出路径，则清理临时目录
            if 'temp_dir' in locals() and not output_path:
                shutil.rmtree(temp_dir, ignore_errors=True)