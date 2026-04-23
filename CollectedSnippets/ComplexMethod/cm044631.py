def __str__(self) -> str:
        """Re-generate style definition from attributes."""
        if self._style_definition is None:
            attributes: List[str] = []
            append = attributes.append
            bits = self._set_attributes
            if bits & 0b0000000001111:
                if bits & 1:
                    append("bold" if self.bold else "not bold")
                if bits & (1 << 1):
                    append("dim" if self.dim else "not dim")
                if bits & (1 << 2):
                    append("italic" if self.italic else "not italic")
                if bits & (1 << 3):
                    append("underline" if self.underline else "not underline")
            if bits & 0b0000111110000:
                if bits & (1 << 4):
                    append("blink" if self.blink else "not blink")
                if bits & (1 << 5):
                    append("blink2" if self.blink2 else "not blink2")
                if bits & (1 << 6):
                    append("reverse" if self.reverse else "not reverse")
                if bits & (1 << 7):
                    append("conceal" if self.conceal else "not conceal")
                if bits & (1 << 8):
                    append("strike" if self.strike else "not strike")
            if bits & 0b1111000000000:
                if bits & (1 << 9):
                    append("underline2" if self.underline2 else "not underline2")
                if bits & (1 << 10):
                    append("frame" if self.frame else "not frame")
                if bits & (1 << 11):
                    append("encircle" if self.encircle else "not encircle")
                if bits & (1 << 12):
                    append("overline" if self.overline else "not overline")
            if self._color is not None:
                append(self._color.name)
            if self._bgcolor is not None:
                append("on")
                append(self._bgcolor.name)
            if self._link:
                append("link")
                append(self._link)
            self._style_definition = " ".join(attributes) or "none"
        return self._style_definition