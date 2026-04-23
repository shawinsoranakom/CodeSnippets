def downgrade(self, system: ColorSystem) -> "Color":
        """Downgrade a color system to a system with fewer colors."""

        if self.type in (ColorType.DEFAULT, system):
            return self
        # Convert to 8-bit color from truecolor color
        if system == ColorSystem.EIGHT_BIT and self.system == ColorSystem.TRUECOLOR:
            assert self.triplet is not None
            _h, l, s = rgb_to_hls(*self.triplet.normalized)
            # If saturation is under 15% assume it is grayscale
            if s < 0.15:
                gray = round(l * 25.0)
                if gray == 0:
                    color_number = 16
                elif gray == 25:
                    color_number = 231
                else:
                    color_number = 231 + gray
                return Color(self.name, ColorType.EIGHT_BIT, number=color_number)

            red, green, blue = self.triplet
            six_red = red / 95 if red < 95 else 1 + (red - 95) / 40
            six_green = green / 95 if green < 95 else 1 + (green - 95) / 40
            six_blue = blue / 95 if blue < 95 else 1 + (blue - 95) / 40

            color_number = (
                16 + 36 * round(six_red) + 6 * round(six_green) + round(six_blue)
            )
            return Color(self.name, ColorType.EIGHT_BIT, number=color_number)

        # Convert to standard from truecolor or 8-bit
        elif system == ColorSystem.STANDARD:
            if self.system == ColorSystem.TRUECOLOR:
                assert self.triplet is not None
                triplet = self.triplet
            else:  # self.system == ColorSystem.EIGHT_BIT
                assert self.number is not None
                triplet = ColorTriplet(*EIGHT_BIT_PALETTE[self.number])

            color_number = STANDARD_PALETTE.match(triplet)
            return Color(self.name, ColorType.STANDARD, number=color_number)

        elif system == ColorSystem.WINDOWS:
            if self.system == ColorSystem.TRUECOLOR:
                assert self.triplet is not None
                triplet = self.triplet
            else:  # self.system == ColorSystem.EIGHT_BIT
                assert self.number is not None
                if self.number < 16:
                    return Color(self.name, ColorType.WINDOWS, number=self.number)
                triplet = ColorTriplet(*EIGHT_BIT_PALETTE[self.number])

            color_number = WINDOWS_PALETTE.match(triplet)
            return Color(self.name, ColorType.WINDOWS, number=color_number)

        return self