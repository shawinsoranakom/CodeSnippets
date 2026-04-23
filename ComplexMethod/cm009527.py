def line(self, x0: int, y0: int, x1: int, y1: int, char: str) -> None:
        """Create a line on ASCII canvas.

        Args:
            x0: x coordinate where the line should start.
            y0: y coordinate where the line should start.
            x1: x coordinate where the line should end.
            y1: y coordinate where the line should end.
            char: character to draw the line with.
        """
        if x0 > x1:
            x1, x0 = x0, x1
            y1, y0 = y0, y1

        dx = x1 - x0
        dy = y1 - y0

        if dx == 0 and dy == 0:
            self.point(x0, y0, char)
        elif abs(dx) >= abs(dy):
            for x in range(x0, x1 + 1):
                y = y0 if dx == 0 else y0 + round((x - x0) * dy / float(dx))
                self.point(x, y, char)
        elif y0 < y1:
            for y in range(y0, y1 + 1):
                x = x0 if dy == 0 else x0 + round((y - y0) * dx / float(dy))
                self.point(x, y, char)
        else:
            for y in range(y1, y0 + 1):
                x = x0 if dy == 0 else x1 + round((y - y1) * dx / float(dy))
                self.point(x, y, char)