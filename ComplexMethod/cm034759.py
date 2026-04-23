async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        media: MediaListType = None,
        **kwargs
    ) -> AsyncResult:
        if media is None:
            raise ValueError("MarkItDown requires media to be provided.")
        if not has_markitdown:
            raise ImportError("MarkItDown is not installed. Please install it with `pip install markitdown`.")
        md = MaItDo()
        for file, filename in media:
            text = None
            try:
                if isinstance(file, str) and file.startswith(("http://", "https://")):
                    result = md.convert_url(file)
                else:
                    result = md.convert(file, stream_info=StreamInfo(filename=filename) if filename else None)
                if asyncio.iscoroutine(result.text_content):
                    text = await result.text_content
                else:
                    text = result.text_content
            except TypeError:
                copyfile = get_tempfile(file, filename)
                try:
                    result = md.convert(copyfile)
                    if asyncio.iscoroutine(result.text_content):
                        text = await result.text_content
                    else:
                        text = result.text_content
                finally:
                    os.remove(copyfile)
            text = text.split("### Audio Transcript:\n")[-1]
            if text:
                yield text