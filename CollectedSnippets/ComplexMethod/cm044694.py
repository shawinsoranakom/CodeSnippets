def _get_pulse_segments(
        self,
        fore_style: Style,
        back_style: Style,
        color_system: str,
        no_color: bool,
        ascii: bool = False,
    ) -> List[Segment]:
        """Get a list of segments to render a pulse animation.

        Returns:
            List[Segment]: A list of segments, one segment per character.
        """
        bar = "-" if ascii else "━"
        segments: List[Segment] = []
        if color_system not in ("standard", "eight_bit", "truecolor") or no_color:
            segments += [Segment(bar, fore_style)] * (PULSE_SIZE // 2)
            segments += [Segment(" " if no_color else bar, back_style)] * (
                PULSE_SIZE - (PULSE_SIZE // 2)
            )
            return segments

        append = segments.append
        fore_color = (
            fore_style.color.get_truecolor()
            if fore_style.color
            else ColorTriplet(255, 0, 255)
        )
        back_color = (
            back_style.color.get_truecolor()
            if back_style.color
            else ColorTriplet(0, 0, 0)
        )
        cos = math.cos
        pi = math.pi
        _Segment = Segment
        _Style = Style
        from_triplet = Color.from_triplet

        for index in range(PULSE_SIZE):
            position = index / PULSE_SIZE
            fade = 0.5 + cos(position * pi * 2) / 2.0
            color = blend_rgb(fore_color, back_color, cross_fade=fade)
            append(_Segment(bar, _Style(color=from_triplet(color))))
        return segments