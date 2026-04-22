def header(
        self, body: SupportsStr, anchor: Optional[str] = None
    ) -> "DeltaGenerator":
        """Display text in header formatting.

        Parameters
        ----------
        body : str
            The text to display.

        anchor : str
            The anchor name of the header that can be accessed with #anchor
            in the URL. If omitted, it generates an anchor using the body.

        Example
        -------
        >>> st.header('This is a header')

        """
        header_proto = HeadingProto()
        if anchor is not None:
            header_proto.anchor = anchor
        header_proto.body = clean_text(body)
        header_proto.tag = "h2"
        return self.dg._enqueue("heading", header_proto)