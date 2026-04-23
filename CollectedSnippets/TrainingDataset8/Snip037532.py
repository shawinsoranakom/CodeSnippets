def caption(
        self, body: SupportsStr, unsafe_allow_html: bool = False
    ) -> "DeltaGenerator":
        """Display text in small font.

        This should be used for captions, asides, footnotes, sidenotes, and
        other explanatory text.

        Parameters
        ----------
        body : str
            The text to display.

        unsafe_allow_html : bool
            By default, any HTML tags found in strings will be escaped and
            therefore treated as pure text. This behavior may be turned off by
            setting this argument to True.

            That said, *we strongly advise against it*. It is hard to write secure
            HTML, so by using this argument you may be compromising your users'
            security. For more information, see:

            https://github.com/streamlit/streamlit/issues/152

        Example
        -------
        >>> st.caption('This is a string that explains something above.')

        """
        caption_proto = MarkdownProto()
        caption_proto.body = clean_text(body)
        caption_proto.allow_html = unsafe_allow_html
        caption_proto.is_caption = True
        return self.dg._enqueue("markdown", caption_proto)