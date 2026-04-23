def title(
        self, body: SupportsStr, anchor: Optional[str] = None
    ) -> "DeltaGenerator":
        """Display text in title formatting.

        Each document should have a single `st.title()`, although this is not
        enforced.

        Parameters
        ----------
        body : str
            The text to display.

        anchor : str
            The anchor name of the header that can be accessed with #anchor
            in the URL. If omitted, it generates an anchor using the body.

        Example
        -------
        >>> st.title('This is a title')

        """
        title_proto = HeadingProto()
        if anchor is not None:
            title_proto.anchor = anchor
        title_proto.body = clean_text(body)
        title_proto.tag = "h1"

        return self.dg._enqueue("heading", title_proto)