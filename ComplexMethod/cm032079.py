def format(self,
               content: str,
               metadata: FileMetadata,
               options: Optional[FoldingOptions] = None) -> str:
        """格式化文件内容"""
        if not metadata.validate():
            raise MetadataError("Invalid file metadata")

        try:
            options = options or FoldingOptions()

            # 构建摘要信息
            summary_parts = [
                f"{metadata.rel_path} ({metadata.size:.2f}MB)",
                f"Type: {metadata.mime_type}" if metadata.mime_type else None,
                (f"Modified: {metadata.last_modified.strftime('%Y-%m-%d %H:%M:%S')}"
                 if metadata.last_modified and options.show_timestamp else None)
            ]
            summary = " | ".join(filter(None, summary_parts))

            # 构建HTML类
            css_class = f' class="{options.custom_css}"' if options.custom_css else ''

            # 格式化内容
            formatted_content = self._format_content_block(content, options)

            # 组装最终结果
            result = (
                f'<details{css_class}><summary>{summary}</summary>\n\n'
                f'{formatted_content}\n\n'
                f'</details>\n\n'
            )

            return self._add_indent(result, options.indent_level)

        except Exception as e:
            logger.error(f"Error formatting file content: {str(e)}")
            raise FormattingError(f"Failed to format file content: {str(e)}")