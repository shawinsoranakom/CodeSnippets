def get_row(
        self,
        widths: Iterable[int],
        level: Literal["head", "row", "foot", "mid"] = "row",
        edge: bool = True,
    ) -> str:
        """Get the top of a simple box.

        Args:
            width (List[int]): Widths of columns.

        Returns:
            str: A string of box characters.
        """
        if level == "head":
            left = self.head_row_left
            horizontal = self.head_row_horizontal
            cross = self.head_row_cross
            right = self.head_row_right
        elif level == "row":
            left = self.row_left
            horizontal = self.row_horizontal
            cross = self.row_cross
            right = self.row_right
        elif level == "mid":
            left = self.mid_left
            horizontal = " "
            cross = self.mid_vertical
            right = self.mid_right
        elif level == "foot":
            left = self.foot_row_left
            horizontal = self.foot_row_horizontal
            cross = self.foot_row_cross
            right = self.foot_row_right
        else:
            raise ValueError("level must be 'head', 'row' or 'foot'")

        parts: List[str] = []
        append = parts.append
        if edge:
            append(left)
        for last, width in loop_last(widths):
            append(horizontal * width)
            if not last:
                append(cross)
        if edge:
            append(right)
        return "".join(parts)