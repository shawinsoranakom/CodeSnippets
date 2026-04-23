def compress_image(self, image_bytes: bytes, mime_type: str, file_path: str):
        """压缩图片，保持合理质量。"""
        try:
            img = Image.open(BytesIO(image_bytes))
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background
            width, height = img.size
            if width > DEFAULT_MAX_WIDTH or height > DEFAULT_MAX_HEIGHT:
                ratio = min(DEFAULT_MAX_WIDTH / width, DEFAULT_MAX_HEIGHT / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            output = BytesIO()
            if mime_type == "image/gif":
                img.save(output, format="GIF", optimize=True)
                output_mime = "image/gif"
            elif mime_type == "image/png":
                img.save(
                    output,
                    format="PNG",
                    optimize=True,
                    compress_level=DEFAULT_PNG_COMPRESS_LEVEL,
                )
                output_mime = "image/png"
            else:
                img.save(
                    output, format="JPEG", quality=DEFAULT_JPEG_QUALITY, optimize=True
                )
                output_mime = "image/jpeg"
            compressed_bytes = output.getvalue()
            return compressed_bytes, output_mime
        except Exception:
            return image_bytes, mime_type