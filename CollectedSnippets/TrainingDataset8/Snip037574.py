def marshall(
    coordinates: str,
    image_list_proto: ImageListProto,
    fig: Optional["Figure"] = None,
    clear_figure: Optional[bool] = True,
    **kwargs: Any,
) -> None:
    try:
        import matplotlib
        import matplotlib.pyplot as plt

        plt.ioff()
    except ImportError:
        raise ImportError("pyplot() command requires matplotlib")

    # You can call .savefig() on a Figure object or directly on the pyplot
    # module, in which case you're doing it to the latest Figure.
    if not fig:
        if clear_figure is None:
            clear_figure = True

        fig = plt

    # Normally, dpi is set to 'figure', and the figure's dpi is set to 100.
    # So here we pick double of that to make things look good in a high
    # DPI display.
    options = {"bbox_inches": "tight", "dpi": 200, "format": "png"}

    # If some options are passed in from kwargs then replace the values in
    # options with the ones from kwargs
    options = {a: kwargs.get(a, b) for a, b in options.items()}
    # Merge options back into kwargs.
    kwargs.update(options)

    image = io.BytesIO()
    fig.savefig(image, **kwargs)
    image_utils.marshall_images(
        coordinates=coordinates,
        image=image,
        caption=None,
        width=-2,
        proto_imgs=image_list_proto,
        clamp=False,
        channels="RGB",
        output_format="PNG",
    )

    # Clear the figure after rendering it. This means that subsequent
    # plt calls will be starting fresh.
    if clear_figure:
        fig.clf()