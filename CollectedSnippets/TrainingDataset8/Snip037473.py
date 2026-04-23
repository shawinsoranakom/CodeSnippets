def _html(
        self,
        html: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        scrolling: bool = False,
    ) -> "DeltaGenerator":
        """Display an HTML string in an iframe.

        Parameters
        ----------
        html : str
            The HTML string to embed in the iframe.
        width : int
            The width of the frame in CSS pixels. Defaults to the app's
            default element width.
        height : int
            The height of the frame in CSS pixels. Defaults to 150.
        scrolling : bool
            If True, show a scrollbar when the content is larger than the iframe.
            Otherwise, do not show a scrollbar. Defaults to False.

        """
        iframe_proto = IFrameProto()
        marshall(
            iframe_proto,
            srcdoc=html,
            width=width,
            height=height,
            scrolling=scrolling,
        )
        return self.dg._enqueue("iframe", iframe_proto)