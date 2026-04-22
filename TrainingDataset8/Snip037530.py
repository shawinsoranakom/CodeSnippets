def markdown(
        self, body: SupportsStr, unsafe_allow_html: bool = False
    ) -> "DeltaGenerator":
        """Display string formatted as Markdown.

        Parameters
        ----------
        body : str
            The string to display as Github-flavored Markdown. Syntax
            information can be found at: https://github.github.com/gfm.

            This also supports:

            * Emoji shortcodes, such as ``:+1:``  and ``:sunglasses:``.
              For a list of all supported codes,
              see https://share.streamlit.io/streamlit/emoji-shortcodes.

            * LaTeX expressions, by wrapping them in "$" or "$$" (the "$$"
              must be on their own lines). Supported LaTeX functions are listed
              at https://katex.org/docs/supported.html.

        unsafe_allow_html : bool
            By default, any HTML tags found in the body will be escaped and
            therefore treated as pure text. This behavior may be turned off by
            setting this argument to True.

            That said, we *strongly advise against it*. It is hard to write
            secure HTML, so by using this argument you may be compromising your
            users' security. For more information, see:

            https://github.com/streamlit/streamlit/issues/152

        Example
        -------
        >>> st.markdown('Streamlit is **_really_ cool**.')

        """
        markdown_proto = MarkdownProto()

        markdown_proto.body = clean_text(body)
        markdown_proto.allow_html = unsafe_allow_html

        return self.dg._enqueue("markdown", markdown_proto)