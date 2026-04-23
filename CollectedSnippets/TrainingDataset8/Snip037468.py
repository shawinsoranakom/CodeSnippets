def subheader(
        self, body: SupportsStr, anchor: Optional[str] = None
    ) -> "DeltaGenerator":
        """Display text in subheader formatting.

        Parameters
        ----------
        body : str
            The text to display.

        anchor : str
            The anchor name of the header that can be accessed with #anchor
            in the URL. If omitted, it generates an anchor using the body.

        Example
        -------
        >>> st.subheader('This is a subheader')

        """
        subheader_proto = HeadingProto()
        if anchor is not None:
            subheader_proto.anchor = anchor
        subheader_proto.body = clean_text(body)
        subheader_proto.tag = "h3"

        return self.dg._enqueue("heading", subheader_proto)