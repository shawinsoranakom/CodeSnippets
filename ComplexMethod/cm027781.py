def __init__(
        self,
        text: str,
        font_size: int = 48,
        height: float | None = None,
        justify: bool = False,
        indent: float = 0,
        alignment: str = "",
        line_width: float | None = None,
        font: str = "",
        slant: str = NORMAL,
        weight: str = NORMAL,
        gradient: Iterable[ManimColor] | None = None,
        line_spacing_height: float | None = None,
        text2color: dict = {},
        text2font: dict = {},
        text2gradient: dict = {},
        text2slant: dict = {},
        text2weight: dict = {},
        # For convenience, one can use shortened names
        lsh: float | None = None,  # Overrides line_spacing_height
        t2c: dict = {},  # Overrides text2color if nonempty
        t2f: dict = {},  # Overrides text2font if nonempty
        t2g: dict = {},  # Overrides text2gradient if nonempty
        t2s: dict = {},  # Overrides text2slant if nonempty
        t2w: dict = {},  # Overrides text2weight if nonempty
        global_config: dict = {},
        local_configs: dict = {},
        disable_ligatures: bool = True,
        isolate: Selector = re.compile(r"\w+", re.U),
        **kwargs
    ):
        text_config = manim_config.text
        self.text = text
        self.font_size = font_size
        self.justify = justify
        self.indent = indent
        self.alignment = alignment or text_config.alignment
        self.line_width = line_width
        self.font = font or text_config.font
        self.slant = slant
        self.weight = weight

        self.lsh = line_spacing_height or lsh
        self.t2c = text2color or t2c
        self.t2f = text2font or t2f
        self.t2g = text2gradient or t2g
        self.t2s = text2slant or t2s
        self.t2w = text2weight or t2w

        self.global_config = global_config
        self.local_configs = local_configs
        self.disable_ligatures = disable_ligatures
        self.isolate = isolate

        super().__init__(text, height=height, **kwargs)

        if self.t2g:
            log.warning("""
                Manim currently cannot parse gradient from svg.
                Please set gradient via `set_color_by_gradient`.
            """)
        if gradient:
            self.set_color_by_gradient(*gradient)
        if self.t2c:
            self.set_color_by_text_to_color_map(self.t2c)
        if height is None:
            self.scale(get_text_mob_scale_factor())