def get_html_style(self, theme: Optional[TerminalTheme] = None) -> str:
        """Get a CSS style rule."""
        theme = theme or DEFAULT_TERMINAL_THEME
        css: List[str] = []
        append = css.append

        color = self.color
        bgcolor = self.bgcolor
        if self.reverse:
            color, bgcolor = bgcolor, color
        if self.dim:
            foreground_color = (
                theme.foreground_color if color is None else color.get_truecolor(theme)
            )
            color = Color.from_triplet(
                blend_rgb(foreground_color, theme.background_color, 0.5)
            )
        if color is not None:
            theme_color = color.get_truecolor(theme)
            append(f"color: {theme_color.hex}")
            append(f"text-decoration-color: {theme_color.hex}")
        if bgcolor is not None:
            theme_color = bgcolor.get_truecolor(theme, foreground=False)
            append(f"background-color: {theme_color.hex}")
        if self.bold:
            append("font-weight: bold")
        if self.italic:
            append("font-style: italic")
        if self.underline:
            append("text-decoration: underline")
        if self.strike:
            append("text-decoration: line-through")
        if self.overline:
            append("text-decoration: overline")
        return "; ".join(css)