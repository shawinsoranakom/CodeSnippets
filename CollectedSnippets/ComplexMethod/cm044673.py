def get_svg_style(style: Style) -> str:
            """Convert a Style to CSS rules for SVG."""
            if style in style_cache:
                return style_cache[style]
            css_rules = []
            color = (
                _theme.foreground_color
                if (style.color is None or style.color.is_default)
                else style.color.get_truecolor(_theme)
            )
            bgcolor = (
                _theme.background_color
                if (style.bgcolor is None or style.bgcolor.is_default)
                else style.bgcolor.get_truecolor(_theme)
            )
            if style.reverse:
                color, bgcolor = bgcolor, color
            if style.dim:
                color = blend_rgb(color, bgcolor, 0.4)
            css_rules.append(f"fill: {color.hex}")
            if style.bold:
                css_rules.append("font-weight: bold")
            if style.italic:
                css_rules.append("font-style: italic;")
            if style.underline:
                css_rules.append("text-decoration: underline;")
            if style.strike:
                css_rules.append("text-decoration: line-through;")

            css = ";".join(css_rules)
            style_cache[style] = css
            return css