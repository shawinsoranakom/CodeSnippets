def code(
        self, body: SupportsStr, language: Optional[str] = "python"
    ) -> "DeltaGenerator":
        """Display a code block with optional syntax highlighting.

        (This is a convenience wrapper around `st.markdown()`)

        Parameters
        ----------
        body : str
            The string to display as code.

        language : str or None
            The language that the code is written in, for syntax highlighting.
            If ``None``, the code will be unstyled. Defaults to ``"python"``.

            For a list of available ``language`` values, see:

            https://github.com/react-syntax-highlighter/react-syntax-highlighter/blob/master/AVAILABLE_LANGUAGES_PRISM.MD

        Example
        -------
        >>> code = '''def hello():
        ...     print("Hello, Streamlit!")'''
        >>> st.code(code, language='python')

        """
        code_proto = MarkdownProto()
        markdown = f'```{language or ""}\n{body}\n```'
        code_proto.body = clean_text(markdown)
        return self.dg._enqueue("markdown", code_proto)