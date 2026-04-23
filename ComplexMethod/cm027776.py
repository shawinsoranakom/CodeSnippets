def __init__(
        self,
        file_name: str = "",
        svg_string: str = "",
        should_center: bool = True,
        height: float | None = None,
        width: float | None = None,
        # Style that overrides the original svg
        color: ManimColor = None,
        fill_color: ManimColor = None,
        fill_opacity: float | None = None,
        stroke_width: float | None = 0.0,
        stroke_color: ManimColor = None,
        stroke_opacity: float | None = None,
        # Style that fills only when not specified
        # If None, regarded as default values from svg standard
        svg_default: dict = dict(
            color=None,
            opacity=None,
            fill_color=None,
            fill_opacity=None,
            stroke_width=None,
            stroke_color=None,
            stroke_opacity=None,
        ),
        path_string_config: dict = dict(),
        **kwargs
    ):
        if svg_string != "":
            self.svg_string = svg_string
        elif file_name != "":
            self.svg_string = self.file_name_to_svg_string(file_name)
        elif self.file_name != "":
            self.svg_string = self.file_name_to_svg_string(self.file_name)
        else:
            raise Exception("Must specify either a file_name or svg_string SVGMobject")

        self.svg_default = dict(svg_default)
        self.path_string_config = dict(path_string_config)

        super().__init__(**kwargs)
        self.init_svg_mobject()
        self.ensure_positive_orientation()

        # Rather than passing style into super().__init__
        # do it after svg has been taken in
        self.set_style(
            fill_color=color or fill_color,
            fill_opacity=fill_opacity,
            stroke_color=color or stroke_color,
            stroke_width=stroke_width,
            stroke_opacity=stroke_opacity,
        )

        # Initialize position
        height = height or self.height
        width = width or self.width

        if should_center:
            self.center()
        if height is not None:
            self.set_height(height)
        if width is not None:
            self.set_width(width)