def parse(cls, color: str) -> "Color":
        """Parse a color definition."""
        original_color = color
        color = color.lower().strip()

        if color == "default":
            return cls(color, type=ColorType.DEFAULT)

        color_number = ANSI_COLOR_NAMES.get(color)
        if color_number is not None:
            return cls(
                color,
                type=(ColorType.STANDARD if color_number < 16 else ColorType.EIGHT_BIT),
                number=color_number,
            )

        color_match = RE_COLOR.match(color)
        if color_match is None:
            raise ColorParseError(f"{original_color!r} is not a valid color")

        color_24, color_8, color_rgb = color_match.groups()
        if color_24:
            triplet = ColorTriplet(
                int(color_24[0:2], 16), int(color_24[2:4], 16), int(color_24[4:6], 16)
            )
            return cls(color, ColorType.TRUECOLOR, triplet=triplet)

        elif color_8:
            number = int(color_8)
            if number > 255:
                raise ColorParseError(f"color number must be <= 255 in {color!r}")
            return cls(
                color,
                type=(ColorType.STANDARD if number < 16 else ColorType.EIGHT_BIT),
                number=number,
            )

        else:  #  color_rgb:
            components = color_rgb.split(",")
            if len(components) != 3:
                raise ColorParseError(
                    f"expected three components in {original_color!r}"
                )
            red, green, blue = components
            triplet = ColorTriplet(int(red), int(green), int(blue))
            if not all(component <= 255 for component in triplet):
                raise ColorParseError(
                    f"color components must be <= 255 in {original_color!r}"
                )
            return cls(color, ColorType.TRUECOLOR, triplet=triplet)