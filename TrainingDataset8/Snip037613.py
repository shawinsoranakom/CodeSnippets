def text(self, body: "SupportsStr") -> "DeltaGenerator":
        """Write fixed-width and preformatted text.

        Parameters
        ----------
        body : str
            The string to display.

        Example
        -------
        >>> st.text('This is some text.')

        """
        text_proto = TextProto()
        text_proto.body = clean_text(body)
        return self.dg._enqueue("text", text_proto)