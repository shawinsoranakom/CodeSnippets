def marshall(
    proto: IFrameProto,
    src: Optional[str] = None,
    srcdoc: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scrolling: bool = False,
) -> None:
    """Marshalls data into an IFrame proto.

    These parameters correspond directly to <iframe> attributes, which are
    described in more detail at
    https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe.

    Parameters
    ----------
    proto : IFrame protobuf
        The protobuf object to marshall data into.
    src : str
        The URL of the page to embed.
    srcdoc : str
        Inline HTML to embed. Overrides src.
    width : int
        The width of the frame in CSS pixels. Defaults to the app's
        default element width.
    height : int
        The height of the frame in CSS pixels. Defaults to 150.
    scrolling : bool
        If true, show a scrollbar when the content is larger than the iframe.
        Otherwise, never show a scrollbar.

    """
    if src is not None:
        proto.src = src

    if srcdoc is not None:
        proto.srcdoc = srcdoc

    if width is not None:
        proto.width = width
        proto.has_width = True

    if height is not None:
        proto.height = height
    else:
        proto.height = 150

    proto.scrolling = scrolling