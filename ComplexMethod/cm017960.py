def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        # Pop our own keyword before forwarding the rest to markdownify.
        # strict=True raises RecursionError instead of falling back to plain text.
        strict: bool = kwargs.pop("strict", False)

        # Parse the stream
        encoding = "utf-8" if stream_info.charset is None else stream_info.charset
        soup = BeautifulSoup(file_stream, "html.parser", from_encoding=encoding)

        # Remove javascript and style blocks
        for script in soup(["script", "style"]):
            script.extract()

        # Print only the main content
        body_elm = soup.find("body")
        webpage_text = ""
        try:
            if body_elm:
                webpage_text = _CustomMarkdownify(**kwargs).convert_soup(body_elm)
            else:
                webpage_text = _CustomMarkdownify(**kwargs).convert_soup(soup)
        except RecursionError:
            if strict:
                raise
            # Large or deeply-nested HTML can exceed Python's recursion limit
            # during markdownify's recursive DOM traversal.  Fall back to
            # BeautifulSoup's iterative get_text() so the caller still gets
            # usable plain-text content instead of raw HTML.
            warnings.warn(
                "HTML document is too deeply nested for markdown conversion "
                "(RecursionError). Falling back to plain-text extraction.",
                stacklevel=2,
            )
            target = body_elm if body_elm else soup
            webpage_text = target.get_text("\n", strip=True)

        assert isinstance(webpage_text, str)

        # remove leading and trailing \n
        webpage_text = webpage_text.strip()

        return DocumentConverterResult(
            markdown=webpage_text,
            title=None if soup.title is None else soup.title.string,
        )