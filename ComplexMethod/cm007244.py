def line(self, x0, y0, x1, y1, char) -> None:
        """Create a line on ASCII canvas."""
        if x0 > x1:
            x1, x0 = x0, x1
            y1, y0 = y0, y1

        dx = x1 - x0
        dy = y1 - y0

        if dx == 0 and dy == 0:
            self.point(x0, y0, char)
        elif abs(dx) >= abs(dy):
            for x in range(x0, x1 + 1):
                y = y0 + round((x - x0) * dy / float(dx)) if dx else y0
                self.point(x, y, char)
        else:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                x = x0 + round((y - y0) * dx / float(dy)) if dy else x0
                self.point(x, y, char)