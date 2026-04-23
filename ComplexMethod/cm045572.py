async def execute(
        self, action: str, file_path: Optional[str] = None, **kwargs
    ) -> ToolResult:
        """
        执行视觉动作，目前仅支持 see_image。
        参数：
            action: 必须为 'see_image'
            file_path: 图片相对路径
        """
        if action != "see_image":
            return self.fail_response(f"未知的视觉动作: {action}")
        if not file_path:
            return self.fail_response("file_path 参数不能为空")
        try:
            await self._ensure_sandbox()
            cleaned_path = self.clean_path(file_path)
            full_path = f"{self.workspace_path}/{cleaned_path}"
            try:
                file_info = self.sandbox.fs.get_file_info(full_path)
                if file_info.is_dir:
                    return self.fail_response(f"路径 '{cleaned_path}' 是目录，不是图片文件。")
            except Exception:
                return self.fail_response(f"图片文件未找到: '{cleaned_path}'")
            if file_info.size > MAX_IMAGE_SIZE:
                return self.fail_response(
                    f"图片文件 '{cleaned_path}' 过大 ({file_info.size / (1024*1024):.2f}MB)，最大允许 {MAX_IMAGE_SIZE / (1024*1024)}MB。"
                )
            try:
                image_bytes = self.sandbox.fs.download_file(full_path)
            except Exception:
                return self.fail_response(f"无法读取图片文件: {cleaned_path}")
            mime_type, _ = mimetypes.guess_type(full_path)
            if not mime_type or not mime_type.startswith("image/"):
                ext = os.path.splitext(cleaned_path)[1].lower()
                if ext == ".jpg" or ext == ".jpeg":
                    mime_type = "image/jpeg"
                elif ext == ".png":
                    mime_type = "image/png"
                elif ext == ".gif":
                    mime_type = "image/gif"
                elif ext == ".webp":
                    mime_type = "image/webp"
                else:
                    return self.fail_response(
                        f"不支持或未知的图片格式: '{cleaned_path}'。支持: JPG, PNG, GIF, WEBP。"
                    )
            compressed_bytes, compressed_mime_type = self.compress_image(
                image_bytes, mime_type, cleaned_path
            )
            if len(compressed_bytes) > MAX_COMPRESSED_SIZE:
                return self.fail_response(
                    f"图片文件 '{cleaned_path}' 压缩后仍过大 ({len(compressed_bytes) / (1024*1024):.2f}MB)，最大允许 {MAX_COMPRESSED_SIZE / (1024*1024)}MB。"
                )
            base64_image = base64.b64encode(compressed_bytes).decode("utf-8")
            image_context_data = {
                "mime_type": compressed_mime_type,
                "base64": base64_image,
                "file_path": cleaned_path,
                "original_size": file_info.size,
                "compressed_size": len(compressed_bytes),
            }
            message = ThreadMessage(
                type="image_context", content=image_context_data, is_llm_message=False
            )
            self.vision_message = message
            # return self.success_response(f"成功加载并压缩图片 '{cleaned_path}' (由 {file_info.size / 1024:.1f}KB 压缩到 {len(compressed_bytes) / 1024:.1f}KB)。")
            return ToolResult(
                output=f"成功加载并压缩图片 '{cleaned_path}'",
                base64_image=base64_image,
            )
        except Exception as e:
            return self.fail_response(f"see_image 执行异常: {str(e)}")